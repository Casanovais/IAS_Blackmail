import google.generativeai as genai
import os
from dotenv import load_dotenv  # <--- Importante!

# Carrega as variáveis do ficheiro .env
load_dotenv()

# Vai buscar a chave ao ambiente carregado
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    print("ERRO: Chave não encontrada. Verifica o teu ficheiro .env")
else:
    genai.configure(api_key=API_KEY)
    print("A verificar modelos disponíveis...")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"Erro: {e}")