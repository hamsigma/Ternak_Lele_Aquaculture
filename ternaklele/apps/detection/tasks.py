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
        confidence_val = hasil["confidence"]
        all_probs = hasil["all_probabilities"]

        log.penyakit_terdeteksi = penyakit_nama
        log.confidence_score = confidence_val
        log.semua_probabilitas = all_probs
        log.status_proses = DetectionLog.Status.DONE

        # 1. Generate Heatmap Grad-CAM jika citra valid teridentifikasi sebagai kelas lele
        if penyakit_nama in classifier.class_labels:
            try:
                import os
                # Buat folder penyimpanan heatmap di MEDIA_ROOT
                date_folder = log.created_at.strftime("%Y/%m") if log.created_at else "live"
                rel_heatmap_path = f"deteksi/heatmaps/{date_folder}/heatmap_{log.id}.jpg"
                full_heatmap_path = os.path.join(settings.MEDIA_ROOT, rel_heatmap_path)
                
                if classifier.generate_heatmap(log.image.path, penyakit_nama, full_heatmap_path):
                    log.heatmap_image = rel_heatmap_path
                    logger.info(f"Grad-CAM berhasil dibuat untuk #{log.id} -> {rel_heatmap_path}")
            except Exception as cam_err:
                logger.warning(f"Gagal generate Grad-CAM untuk #{log.id}: {cam_err}")

        # 2. Logika Triase Klinis & Peringatan Keselamatan (Clinical Safety Protocol)
        triage_notes = []
        if penyakit_nama == "Bukan Lele":
            log.rekomendasi_penanganan = (
                "Sistem AI tidak dapat mendeteksi ikan lele pada gambar ini. "
                "Pastikan Anda mengunggah foto ikan lele yang jelas, terfokus, "
                "dan memiliki pencahayaan yang baik agar AI dapat menganalisis "
                "kondisi kesehatan lele dengan akurat."
            )
            log.triage_warning = (
                "⚠️ Objek visual tidak memenuhi parameter spektral anatomi ikan lele "
                "atau citra terlalu buram/sintetis. Silakan unggah foto tubuh lele asli."
            )
        else:
            # Rekomendasi medis dari database
            try:
                penyakit = Penyakit.objects.get(nama__iexact=penyakit_nama)
                log.rekomendasi_penanganan = penyakit.penanganan
            except Penyakit.DoesNotExist:
                log.rekomendasi_penanganan = "Konsultasikan dengan pakar perikanan untuk penanganan lebih lanjut."

            # A. Triase Darurat Aeromonas hydrophila (Mohamad et al., 2022)
            aero_prob = all_probs.get("Aeromonas", 0.0)
            if penyakit_nama == "Aeromonas" or aero_prob >= 0.12:
                triage_notes.append(
                    f"🚨 PROTOKOL TRIASE DARURAT (Aeromonas hydrophila - {aero_prob*100:.1f}%): "
                    "Bakteri patogen ini memicu septicemia hemoragik akut dengan laju mortalitas (LD50) sangat cepat (Mohamad et al., 2022). "
                    "Tindakan segera: (1) Karantina lele sakit, (2) Lakukan pergantian air bertahap 30-50%, "
                    "(3) Berikan perendaman garam ikan non-beryodium (1-3 g/L) atau antibakteri terdaftar dinas perikanan."
                )

            # B. Peringatan Manajemen Pakan & Distensi Abdomen (Dwi Apriyani, 2025)
            if penyakit_nama == "Overfeeding":
                triage_notes.append(
                    "⚠️ PERINGATAN TATA KELOLA PAKAN (Overfeeding): "
                    "Terdeteksi pembengkakan perut akibat pakan berlebih (Dwi Apriyani, 2025). "
                    "Puasakan lele selama 24 jam untuk melancarkan saluran cerna dan segera bersihkan endapan "
                    "sisa pakan di dasar kolam guna mencegah pembusukan serta lonjakan amonia beracun."
                )

            # C. Safety Warning jika skor keyakinan di bawah 80%
            if confidence_val < 0.80:
                triage_notes.append(
                    f"⚠️ PERINGATAN OBSERVASI MANUAL (< 80%): "
                    f"Skor keyakinan model berada pada {confidence_val*100:.1f}%. "
                    "Peternak sangat disarankan melakukan observasi visual manual terhadap kelincahan renang lele, "
                    "respons nafsu makan, serta memeriksa parameter air kolam (pH, DO, suhu)."
                )

            log.triage_warning = "\n\n".join(triage_notes)

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
