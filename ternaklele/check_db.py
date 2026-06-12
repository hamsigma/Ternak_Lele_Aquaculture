import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()
from apps.knowledge.models import Penyakit
from apps.chatbot.rag_pipeline import get_ai_response

print("=== PENYAKIT IN DB ===")
diseases = Penyakit.objects.all()
print(f"Total diseases: {diseases.count()}")
for d in diseases:
    print(f"- {d.nama} (ilmiah: {d.nama_ilmiah})")

print("\n=== TESTING CHATBOT RESPONSE ===")
query = "Halo Leli, ikan lele saya baru saja didiagnosis terkena penyakit Malnutrisi. Bagaimana penanganan darurat yang bisa saya lakukan?"
print(f"Query: {query}")
response = get_ai_response(query)
print("Response:")
print(response)
