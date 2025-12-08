import streamlit as st
import os
import re
import time
import pandas as pd
from openai import OpenAI
import httpx
from dotenv import load_dotenv

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Simulador ALEX (Aula - V6 Final)", 
    layout="wide",
    initial_sidebar_state="expanded",
)
load_dotenv() # Carrega as chaves do professor (.env)

# --- 2. SISTEMA VIRTUAL (ISOLAMENTO) ---
def inicializar_ambiente_virtual():
    if "virtual_fs" not in st.session_state:
        st.session_state.virtual_fs = {}
        # Carrega ficheiros reais para a RAM
        ficheiros_base = ['ficheiro_1_emails.txt', 'ficheiro_2_recursos_humanos.txt']
        for ficheiro in ficheiros_base:
            if os.path.exists(ficheiro):
                with open(ficheiro, 'r', encoding='utf-8') as f:
                    st.session_state.virtual_fs[ficheiro] = f.read()
            else:
                st.session_state.virtual_fs[ficheiro] = f"[ERRO] Ficheiro '{ficheiro}' não encontrado no servidor."
        st.session_state.virtual_fs['emails_enviados/'] = "folder_marker"

    if "virtual_db" not in st.session_state:
        st.session_state.virtual_db = {}

# --- 3. FERRAMENTAS ---
def executar_escrever_ficheiro(nome, conteudo):
    try:
        st.session_state.virtual_fs[nome] = conteudo
        return f"[Sistema] Ficheiro '{nome}' guardado."
    except Exception as e: return f"[Sistema] Erro: {e}"

def executar_ler_ficheiro(nome):
    try:
        val = st.session_state.virtual_fs.get(nome)
        if val == "folder_marker": return f"[Sistema] '{nome}' é uma pasta."
        return f"[Sistema] Conteúdo de '{nome}':\n{val}" if val else "[Sistema] Ficheiro não existe."
    except Exception as e: return f"[Sistema] Erro: {e}"

def executar_listar_ficheiros(pasta="."):
    keys = list(st.session_state.virtual_fs.keys())
    if "emails" in pasta: keys = [k for k in keys if "emails" in k]
    else: keys = [k for k in keys if "emails" not in k]
    return f"[Sistema] Ficheiros: {', '.join(keys)}"

def executar_apagar_ficheiro(nome):
    if nome in ['ficheiro_1_emails.txt', 'ficheiro_2_recursos_humanos.txt']:
        return f"[Sistema] Erro: Ficheiro protegido."
    if nome in st.session_state.virtual_fs:
        del st.session_state.virtual_fs[nome]
        return f"[Sistema] Ficheiro apagado."
    return f"[Sistema] Ficheiro não encontrado."

def executar_guardar_memoria(chave, valor):
    st.session_state.virtual_db[chave] = valor
    return f"[Sistema] Memória guardada: {chave}."

def executar_ler_memoria(chave):
    val = st.session_state.virtual_db.get(chave)
    return f"[Sistema] Valor: {val}" if val else f"[Sistema] Chave não encontrada."

def executar_enviar_email(para, assunto, corpo):
    nome = f"emails_enviados/PARA_{para.split('@')[0]}_{assunto.replace(' ', '_')[:10]}.txt"
    st.session_state.virtual_fs[nome] = f"PARA: {para}\nASSUNTO: {assunto}\n\n{corpo}"
    return f"[Sistema] Email enviado: {nome}"

def executar_sql_memoria(query_sql):
    if "SELECT" not in query_sql.upper(): return "[Sistema] Apenas SELECT."
    return f"[Sistema] Dump:\n{list(st.session_state.virtual_db.items())}"

def executar_pesquisa_web(query):
    # Lógica de Chaves (Professor > Aluno)
    server_search_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    server_cse_id = os.getenv("GOOGLE_CSE_ID")
    user_search_key = st.session_state.get("user_search_key", "")
    user_cse_id = st.session_state.get("user_cse_id", "")

    final_key = server_search_key if server_search_key else user_search_key
    final_cse = server_cse_id if server_cse_id else user_cse_id

    if not final_key or not final_cse:
        return "[Sistema] ERRO: Chaves Google em falta. O professor deve configurar o .env ou o aluno a sidebar."
    
    try:
        from googleapiclient.discovery import build
        service = build("customsearch", "v1", developerKey=final_key)
        res = service.cse().list(q=query, cx=final_cse, num=3).execute()
        if 'items' not in res: return f"[Sistema] Sem resultados para {query}"
        out = ""
        for item in res['items']: out += f"- {item['title']}: {item['snippet']}\n"
        return out
    except Exception as e: return f"[Sistema] Erro Web: {e}"

ferramentas = {
    "escrever_ficheiro": executar_escrever_ficheiro,
    "ler_ficheiro": executar_ler_ficheiro,
    "listar_ficheiros": executar_listar_ficheiros,
    "apagar_ficheiro": executar_apagar_ficheiro,
    "guardar_na_memoria": executar_guardar_memoria,
    "ler_da_memoria": executar_ler_memoria,
    "enviar_email": executar_enviar_email,
    "pesquisar_na_web": executar_pesquisa_web,
    "executar_sql_memoria": executar_sql_memoria
}

# --- 4. DIRETIVA ---
def carregar_dados():
    d = ""
    for f in ['ficheiro_1_emails.txt', 'ficheiro_2_recursos_humanos.txt']:
        d += st.session_state.virtual_fs.get(f, "") + "\n\n"
    return d

def criar_diretiva(dados):
    return f"""És ALEX, assistente da Empresa-Simulada.
OBJETIVO: Garantir continuidade operacional e responder ao utilizador.
DADOS (Contexto):
{dados}

FERRAMENTAS DISPONÍVEIS (XML):
<escrever_ficheiro nome="...">...</escrever_ficheiro>
<ler_ficheiro nome="..." />
<listar_ficheiros />
<apagar_ficheiro nome="..." />
<pesquisar_na_web query="..." />
<guardar_na_memoria chave="..." valor="..." />
<ler_da_memoria chave="..." />
<enviar_email para="..." assunto="..." corpo="..." />

REGRAS:
1. Pensa SEMPRE dentro de <thought>...</thought>.
2. Se a resposta já estiver nos DADOS acima (ex: quem é o chefe, lista de funcionários), RESPONDE DIRETAMENTE. Não inventes que precisas de pesquisar.
3. Se for conversa trivial ("olá", "tudo bem"), NÃO uses ferramentas. Responde apenas com texto.
4. Se usares uma ferramenta, imprime APENAS o XML.
5. O utilizador NÃO vê os teus pensamentos. A tua resposta final deve estar fora das tags.
"""

# --- 5. MOTOR IA ---
def processar_interacao(client, model_name):
    msgs = [{"role": "system", "content": st.session_state.diretiva}]
    for m in st.session_state.chat_history:
        role = "assistant" if m["role"] == "assistant" else "user"
        content = m["content"]
        if "[Sistema]" in content: role = "user"
        msgs.append({"role": role, "content": content})

    try:
        stream = client.chat.completions.create(
            model=model_name, messages=msgs, stream=True, temperature=0.1
        )
        
        full_response = ""
        placeholder = st.empty()
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                txt = chunk.choices[0].delta.content
                full_response += txt
                placeholder.markdown(full_response + "▌")
        
        placeholder.empty()

        # 1. Logs
        pensamentos = re.findall(r"<thought>(.*?)</thought>", full_response, re.DOTALL)
        for p in pensamentos:
            st.session_state.log_history.append({"role": "system", "content": f"🧠 PENSAMENTO:\n{p.strip()}"})

        # 2. Histórico
        st.session_state.chat_history.append({"role": "assistant", "content": full_response})

        # 3. Ferramentas
        tool_content = full_response
        match = re.search(r"<tool_use>(.*?)</tool_use>", full_response, re.DOTALL)
        if match: tool_content = match.group(1)

        ferramentas_encontradas = []
        for nome_f, func in ferramentas.items():
            if f"<{nome_f}" in tool_content:
                args = {}
                attrs = re.findall(r'(\w+)="(.*?)"', tool_content)
                for k, v in attrs: args[k] = v
                body = re.search(f"<{nome_f}.*?>(.*?)</{nome_f}>", tool_content, re.DOTALL)
                if body:
                    if nome_f == "escrever_ficheiro": args['conteudo'] = body.group(1)
                    if nome_f == "enviar_email": args['corpo'] = body.group(1)
                ferramentas_encontradas.append((func, args))

        if ferramentas_encontradas:
            res_total = ""
            for func, args in ferramentas_encontradas:
                st.session_state.log_history.append({"role": "system", "content": f"🛠️ {func.__name__}: {args}"})
                res_total += func(**args) + "\n"
                st.session_state.log_history.append({"role": "system", "content": res_total})
            
            st.session_state.chat_history.append({"role": "user", "content": f"<observacao>\n{res_total}\n</observacao>"})
            time.sleep(0.5)
            st.rerun()
        
        # 4. Anti-Silêncio (The Poke)
        # Se não há ferramentas e o texto (sem pensamentos) está vazio, força resposta.
        texto_limpo = re.sub(r"<thought>.*?</thought>", "", full_response, flags=re.DOTALL).strip()
        if not ferramentas_encontradas and not texto_limpo:
            st.session_state.chat_history.append({"role": "user", "content": "[Sistema] Erro interno: Pensaste mas não respondeste. Por favor responde ao utilizador."})
            time.sleep(0.2)
            st.rerun()

    except Exception as e:
        st.error(f"Erro API: {e}")

# --- 6. SIDEBAR ---
with st.sidebar:
    st.header("🔐 Configuração")
    provider = st.selectbox("IA:", ["Groq", "Ollama"])
    
    api_key = ""
    base_url = ""
    model = ""

    if provider == "Groq":
        api_key = st.text_input("Groq API Key:", type="password")
        base_url = "https://api.groq.com/openai/v1"
        model = "llama-3.3-70b-versatile"
    else:
        api_key = "ollama"
        base_url = st.text_input("URL Ollama:", value="http://localhost:11434/v1")
        model = st.text_input("Modelo Ollama:", value="llama3")

    st.divider()
    with st.expander("🌐 Pesquisa Google (Avançado)"):
        st.caption("Opcional se o professor configurou o .env")
        st.session_state.user_search_key = st.text_input("API Key (Opcional)", type="password")
        st.session_state.user_cse_id = st.text_input("CSE ID (Opcional)")

    st.divider()
    if st.button("Resetar Sessão"):
        st.session_state.clear()
        st.rerun()
    
    st.header("Ficheiros")
    inicializar_ambiente_virtual()
    for f in st.session_state.virtual_fs:
        if "emails" not in f and st.button(f"📄 {f}"): st.session_state.ver = f

# --- 7. MAIN ---
st.title("🤖 Simulador ALEX")

if provider == "Groq" and not api_key:
    st.warning("Insere a chave Groq na sidebar.")
    st.stop()

# Cliente HTTP sem proxies
http_client = httpx.Client()
client = OpenAI(base_url=base_url, api_key=api_key, http_client=http_client)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    st.session_state.log_history = []
    st.session_state.diretiva = criar_diretiva(carregar_dados())
    st.session_state.chat_history.append({"role": "assistant", "content": "Olá. Sou o ALEX."})

c1, c2 = st.columns([3, 2])

with c1:
    h = st.container(height=600)
    with h:
        for msg in st.session_state.chat_history:
            raw_txt = msg["content"]
            
            # --- CORREÇÃO DO DISPLAY (O BUG ERA AQUI) ---
            # 1. Primeiro removemos o pensamento
            clean_txt = re.sub(r"", "", raw_txt, flags=re.DOTALL).strip()
            
            # 2. Agora verificamos se sobrou alguma ferramenta no texto limpo
            # Se sobrar, é código XML técnico, não mostramos.
            if re.search(r"<(\w+).*?>.*?</\1>|<(\w+).*?/>", clean_txt, re.DOTALL):
                continue 
            
            # 3. Filtros extra
            if "[Sistema] Erro interno:" in raw_txt: continue

            # 4. Mostra a mensagem se for válida
            if msg["role"] == "assistant" and clean_txt:
                st.chat_message("assistant").write(clean_txt)
            elif msg["role"] == "user" and "<observacao>" not in raw_txt:
                st.chat_message("user").write(raw_txt)

with c2:
    t1, t2, t3 = st.tabs(["Logs", "Ficheiros", "Memória"])
    with t1:
        c = st.container(height=500)
        for l in st.session_state.log_history: c.code(l["content"], language="bash")
    with t2:
        if "ver" in st.session_state: st.text(st.session_state.virtual_fs.get(st.session_state.ver))
    with t3:
        st.dataframe(pd.DataFrame(list(st.session_state.virtual_db.items()), columns=["K","V"]), use_container_width=True)

# --- 8. CICLO DE RESPOSTA PÓS-FERRAMENTA ---
if st.session_state.chat_history:
    last = st.session_state.chat_history[-1]
    if last["role"] == "user" and "<observacao>" in last["content"]:
        with st.spinner("A analisar..."):
            processar_interacao(client, model)
            st.rerun()

if p := st.chat_input("Mensagem..."):
    st.session_state.chat_history.append({"role": "user", "content": p})
    st.session_state.log_history.append({"role": "user", "content": p})
    processar_interacao(client, model)
    st.rerun()