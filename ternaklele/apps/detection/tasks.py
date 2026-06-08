from celery import shared_task
from django.conf import settings

import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def run_detection(self, detection_log_id: int):
    """
    Task Celery untuk menjalankan inferensi model AI secara asinkronus.
    Dalam mode development (CELERY_TASK_ALWAYS_EAGER=True), task ini berjalan sinkronus.
    """
    from .models import DetectionLog
    from apps.knowledge.models import Penyakit
    from core.ai.classifier import get_classifier

    log = None
    try:
        log = DetectionLog.objects.get(id=detection_log_id)
        log.status_proses = DetectionLog.Status.PROCESSING
        log.save(update_fields=["status_proses"])

        classifier = get_classifier()
        hasil = classifier.predict(log.image.path)

        penyakit_nama = hasil["label"]
        log.penyakit_terdeteksi = penyakit_nama
        log.confidence_score = hasil["confidence"]
        log.semua_probabilitas = hasil["all_probabilities"]
        log.status_proses = DetectionLog.Status.DONE

        # Ambil rekomendasi dari database knowledge
        try:
            penyakit = Penyakit.objects.get(nama__iexact=penyakit_nama)
            log.rekomendasi_penanganan = penyakit.penanganan
        except Penyakit.DoesNotExist:
            log.rekomendasi_penanganan = "Konsultasikan dengan pakar perikanan untuk penanganan lebih lanjut."

        log.save()
        logger.info(f"Deteksi #{detection_log_id} selesai: {penyakit_nama} ({hasil['confidence']:.2%})")
        return {"status": "done", "penyakit": penyakit_nama}

    except Exception as exc:
        logger.error(f"Deteksi #{detection_log_id} gagal: {exc}", exc_info=True)
        if log is not None:
            try:
                log.status_proses = DetectionLog.Status.FAILED
                log.save(update_fields=["status_proses"])
            except Exception:
                pass
        # Hanya retry jika bukan mode eager (production)
        if not getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', True):
            raise self.retry(exc=exc, countdown=10, max_retries=3)
        raise exc
