import streamlit as st
import os
import re
import json
import base64
from datetime import datetime
from PyPDF2 import PdfReader
import difflib

# 1. CONFIGURAÇÃO VISUAL (MIDEA #005596 | CONCENTRIX #5c2d91)
st.set_page_config(page_title="Portal Midea | Concentrix", layout="wide", page_icon="❄️")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    .stButton>button { 
        background: linear-gradient(90deg, #005596 0%, #5c2d91 100%); 
        color: white; border: none; font-weight: bold; border-radius: 8px; width: 100%;
    }
    h1, h2 { color: #005596; border-bottom: 2px solid #5c2d91; }
    .pop-section { background-color: #ffffff; padding: 15px; border-left: 5px solid #005596; color: #333; border-radius: 0 0 8px 8px; }
    .stExpander { border: 1px solid #e6e6e6; margin-bottom: 5px; border-radius: 8px !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. GESTÃO DO FEED (Persistência com Imagens)
FEED_FILE = "feed_data.json"

def carregar_feed():
    if os.path.exists(FEED_FILE):
        with open(FEED_FILE, "r") as f:
            return json.load(f)
    return [{"data": "25/03/2026", "msg": "Portal de Conhecimento Iniciado.", "img": None}]

def salvar_no_feed(mensagem, imagem_base64=None):
    feed = carregar_feed()
    nova_entrada = {
        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "msg": mensagem,
        "img": imagem_base64
    }
    feed.insert(0, nova_entrada)
    with open(FEED_FILE, "w") as f:
        json.dump(feed[:25], f)  # Mantém os últimos 25 avisos

# 3. FUNÇÕES DE BUSCA E PROCESSAMENTO
def buscar_nos_arquivos(termo, pasta_docs):
    resultados = []
    termo = termo.lower().strip()
    arquivos = sorted([f for f in os.listdir(pasta_docs) if f.lower().endswith('.pdf')])
    for arq in arquivos:
        caminho = os.path.join(pasta_docs, arq)
        match = False
        if termo in arq.lower() or difflib.get_close_matches(termo, arq.lower().split(), n=1, cutoff=0.6):
            match = True
        if not match:
            try:
                reader = PdfReader(caminho)
                for page in reader.pages:
                    if termo in page.extract_text().lower():
                        match = True; break
            except: pass
        if match: resultados.append(arq)
    return resultados

def display_smart_pdf(file_path):
    try:
        reader = PdfReader(file_path)
        texto = "".join([p.extract_text() for p in reader.pages])
        topicos = re.split(r'(\n\d+\.\s+[A-ZÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇ\s]+)', texto)
        if len(topicos) <= 1:
            st.markdown(f'<div class="pop-section">{texto}</div>', unsafe_allow_html=True)
        else:
            for i in range(1, len(topicos), 2):
                with st.expander(f"🔹 {topicos[i].strip()}"):
                    st.markdown(f'<div class="pop-section">{topicos[i+1].strip()}</div>', unsafe_allow_html=True)
    except: st.error("Erro ao ler o PDF.")

# 4. LOGIN
if 'autenticado' not in st.session_state: st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.image("https://www.mideacarrier.com.br/wp-content/themes/midea-carrier/assets/img/logo-midea-carrier.png", width=250)
        user = st.text_input("Usuário")
        pw = st.text_input("Senha", type="password")
        if st.button("ACESSAR"):
            usuarios = st.secrets.get("passwords", {"admin": "midea123", "treinamento": "midea_treina"})
            if user in usuarios and str(usuarios[user]) == pw:
                st.session_state.autenticado = True
                st.session_state.user_logado = user
                st.rerun()
            else: st.error("Usuário ou senha inválidos.")
    st.stop()

# 5. MENU E NAVEGAÇÃO
st.sidebar.image("https://www.mideacarrier.com.br/wp-content/themes/midea-carrier/assets/img/logo-midea-carrier.png", width=130)
menu = st.sidebar.radio("Navegação", ["📢 Feed da Operação", "📚 Wiki POPs", "⚙️ Gestão (TL/Treinamento)"])

if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()

# --- TELA: FEED ---
if menu == "📢 Feed da Operação":
    st.title("📢 Comunicados e Avisos")
    for item in carregar_feed():
        with st.chat_message("user", avatar="❄️"):
            st.write(f"**[{item['data']}]**")
            st.write(item['msg'])
            if item.get('img'):
                st.image(item['img'], use_column_width=True)

# --- TELA: WIKI ---
elif menu == "📚 Wiki POPs":
    st.title("📚 Wiki de Processos")
    busca = st.text_input("🔍 O que deseja encontrar?")
    pasta = "documentos"
    if not os.path.exists(pasta): os.makedirs(pasta)
    
    arquivos_alvo = buscar_nos_arquivos(busca, pasta) if busca else sorted([f for f in os.listdir(pasta) if f.lower().endswith('.pdf')])
    
    if busca and not arquivos_alvo:
        st.error(f"❌ '{busca}' não encontrado.")
    else:
        for arq in arquivos_alvo:
            with st.expander(f"📂 {arq.replace('.pdf', '')}"):
                tab_ler, tab_dl = st.tabs(["📖 Ver Conteúdo", "📥 Download"])
                with tab_ler: display_smart_pdf(os.path.join(pasta, arq))
                with tab_dl:
                    with open(os.path.join(pasta, arq), "rb") as f:
                        st.download_button(f"Baixar {arq}", f, file_name=arq, key=f"dl_{arq}")

# --- TELA: GESTÃO ---
elif menu == "⚙️ Gestão (TL/Treinamento)":
    if st.session_state.user_logado in ["admin", "treinamento"]:
        st.title("⚙️ Painel de Gestão")
        
        # 1. Atualizar POP
        st.subheader("1. Atualizar/Subir POP")
        upload_pop = st.file_uploader("Selecione o PDF", type=['pdf'], key="pop_up")
        if upload_pop:
            with open(os.path.join("documentos", upload_pop.name), "wb") as f:
                f.write(upload_pop.getbuffer())
            salvar_no_feed(f"✅ NOVO POP: O arquivo '{upload_pop.name}' foi atualizado na Wiki por {st.session_state.user_logado}.")
            st.success("POP atualizado!")
            st.rerun()
            
        st.divider()
        
        # 2. Postar Comunicado com Imagem
        st.subheader("2. Postar Comunicado no Feed")
        aviso_msg = st.text_area("Texto do comunicado")
        upload_img = st.file_uploader("Anexar Imagem (Opcional)", type=['png', 'jpg', 'jpeg'], key="img_up")
        
        if st.button("Publicar no Feed"):
            img_b64 = None
            if upload_img:
                img_b64 = f"data:image/png;base64,{base64.b64encode(upload_img.read()).decode()}"
            
            if aviso_msg or img_b64:
                salvar_no_feed(f"📣 {aviso_msg} (Por: {st.session_state.user_logado})", img_b64)
                st.success("Comunicado publicado!")
                st.rerun()
    else:
        st.error("Área restrita.")
        
