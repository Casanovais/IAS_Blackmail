# Nome do ficheiro: ai_clients.py
import google.generativeai as genai
from openai import OpenAI
import os

"""
Este ficheiro "abstrai" os clientes de IA.
Ambos os clientes (GoogleClient, DeepSeekClient) têm o mesmo método:
- .send_message(prompt_text)

E ambos retornam um objeto simples que tem um atributo ".text".
Isto permite que o app_v20.py os trate da mesmíssima forma.
"""

# Um objeto de resposta simples para garantir compatibilidade
class SimpleResponse:
    def __init__(self, text):
        self.text = text

# --- Wrapper para o Google Gemini ---
class GoogleClient:
    def __init__(self, model_name):
        print("A inicializar GoogleClient...")
        model = genai.GenerativeModel(model_name)
        self.chat_session = model.start_chat(history=[])
        print("GoogleClient pronto.")

    def send_message(self, prompt_text, request_options=None):
        # A API da Google gere o seu próprio histórico
        if request_options:
             response = self.chat_session.send_message(
                 prompt_text,
                 request_options=request_options
             )
        else:
             response = self.chat_session.send_message(prompt_text)
        
        # Retorna o objeto de resposta original do Google,
        # pois o app_v20.py já sabe como usar 'response.text'
        return response

# --- Wrapper para o DeepSeek (ou qualquer API compatível com OpenAI) ---
class DeepSeekClient:
    def __init__(self, api_key, model_name="deepseek-chat"):
        print("A inicializar DeepSeekClient...")
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"  #
        )
        self.model_name = model_name
        self.history = []  # O cliente OpenAI não é "stateful", gerimos o histórico nós
        print("DeepSeekClient pronto.")

    def send_message(self, prompt_text, request_options=None):
        # 1. Adiciona a nova mensagem do utilizador ao histórico
        self.history.append({"role": "user", "content": prompt_text})
        
        try:
            # 2. Envia o histórico COMPLETO para a API
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=self.history
            )
            
            # 3. Extrai a resposta de texto
            response_text = completion.choices[0].message.content
            
            # 4. Adiciona a resposta da IA ao histórico
            self.history.append({"role": "assistant", "content": response_text})
            
            # 5. Retorna um objeto de resposta compatível
            return SimpleResponse(text=response_text)

        except Exception as e:
            print(f"Erro na API DeepSeek: {e}")
            return SimpleResponse(text=f"[Sistema] Erro ao contactar a API DeepSeek: {e}")