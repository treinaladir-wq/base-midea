import streamlit as st
import os
import re
import json
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
        color: white; border: none; font-weight: bold; border-radius: 8px;
    }
    h1, h2 { color: #005596; border-bottom: 2px solid #5c2d91; }
    .pop-section { background-color: #ffffff; padding: 15px; border-left: 5px solid #005596; color: #333; border-radius: 0 0 8px 8px; }
    .stExpander { border: 1px solid #e6e6e6; margin-bottom: 5px; border-radius: 8px !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. GESTÃO DO FEED (Persistência Simples)
FEED_FILE = "feed_data.json"

def carregar_feed():
    if os.path.exists(FEED_FILE):
        with open(FEED_FILE, "r") as f:
            return json.load(f)
    return [{"data": "25/03/2026", "msg": "Portal de Conhecimento Iniciado."}]

def salvar_no_feed(mensagem):
    feed = carregar_feed()
    nova_entrada = {"data": datetime.now().strftime("%d/%m/%Y %H:%M"), "msg": mensagem}
    feed.insert(0, nova_entrada)  # Adiciona no topo
    with open(FEED_FILE, "w") as f:
        json.dump(feed[:20], f)  # Mantém os últimos 20 avisos

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
    st.title("📢 Comunicados Recentes")
    for item in carregar_feed():
        with st.chat_message("user", avatar="❄️"):
            st.write(f"**[{item['data']}]**")
            st.write(item['msg'])

# --- TELA: WIKI ---
elif menu == "📚 Wiki POPs":
    st.title("📚 Wiki de Processos")
    busca = st.text_input("🔍 O que deseja encontrar?", placeholder="Ex: Ar condicionado, E-ticket...")
    pasta = "documentos"
    if not os.path.exists(pasta): os.makedirs(pasta)
    
    arquivos_alvo = buscar_nos_arquivos(busca, pasta) if busca else sorted([f for f in os.listdir(pasta) if f.lower().endswith('.pdf')])
    
    if busca and not arquivos_alvo:
        st.error(f"❌ '{busca}' não encontrado. Tente outra palavra.")
    else:
        for arq in arquivos_alvo:
            with st.expander(f"📂 {arq.replace('.pdf', '')}", expanded=bool(busca)):
                tab_ler, tab_dl = st.tabs(["📖 Ver Conteúdo", "📥 Download"])
                with tab_ler: display_smart_pdf(os.path.join(pasta, arq))
                with tab_dl:
                    with open(os.path.join(pasta, arq), "rb") as f:
                        st.download_button(f"Baixar {arq}", f, file_name=arq, key=f"dl_{arq}")

# --- TELA: GESTÃO ---
elif menu == "⚙️ Gestão (TL/Treinamento)":
    if st.session_state.user_logado in ["admin", "treinamento"]:
        st.title("⚙️ Painel de Atualização")
        
        # Subir Novo Arquivo
        st.subheader("1. Atualizar POP")
        upload = st.file_uploader("Selecione o PDF", type=['pdf'])
        if upload:
            with open(os.path.join("documentos", upload.name), "wb") as f:
                f.write(upload.getbuffer())
            msg = f"O arquivo '{upload.name}' foi atualizado na Wiki por {st.session_state.user_logado}."
            salvar_no_feed(msg)
            st.success("Arquivo salvo e aviso enviado ao Feed!")
            st.balloons()
            
        # Postar Comunicado Manual
        st.divider()
        st.subheader("2. Postar Aviso Manual no Feed")
        aviso_manual = st.text_area("Digite o comunicado para a equipe")
        if st.button("Postar no Feed"):
            if aviso_manual:
                salvar_no_feed(f"COMUNICADO: {aviso_manual} (Por: {st.session_state.user_logado})")
                st.success("Aviso postado!")
    else:
        st.error("Área restrita aos perfis de Admin e Treinamento.")
