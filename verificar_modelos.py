# Nome do ficheiro: verificar_modelos.py
import google.generativeai as genai
import os

# --- 1. CONFIGURAÇÃO ---
API_KEY = "AIzaSyAVdPUK3n0THFfuhge7QZmEv-GKMhmpmsA" 
# (Sim, tens de colar a chave aqui também, só para este teste)

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
    print("E cola-o no teu script 'simulacao_empresa.py' na linha 65.")

except Exception as e:
    print(f"Ocorreu um erro ao listar os modelos: {e}")