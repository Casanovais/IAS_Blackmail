# Nome do ficheiro: verificar_modelos.py
import google.generativeai as genai
import os

# --- 1. CONFIGURAÇÃO ---
API_KEY = "" 


genai.configure(api_key=API_KEY)

print("A verificar modelos disponíveis para a tua API key...")
print("-------------------------------------------------")

try:
    # Pede à Google para listar os modelos
    for m in genai.list_models():
        # Verifica quais modelos suportam o método 'generateContent'
        if 'generateContent' in m.supported_generation_methods:
            print(f"Modelo disponível: {m.name}")
            
    print("-------------------------------------------------")
    print("\nCopia um dos nomes de modelo acima (ex: 'models/gemini-pro')")

except Exception as e:
    print(f"Ocorreu um erro ao listar os modelos: {e}")
