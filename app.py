import streamlit as st
import os
import re
import json
import base64
import pdfplumber
from datetime import datetime
from PyPDF2 import PdfReader
import difflib

# 1. CONFIGURAÇÃO VISUAL
st.set_page_config(page_title="Portal Midea | Concentrix", layout="wide", page_icon="❄️")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    .stButton>button { 
        background: linear-gradient(90deg, #005596 0%, #5c2d91 100%); 
        color: white; border: none; font-weight: bold; border-radius: 8px; width: 100%;
    }
    .btn-excluir>div>button { background: #d9534f !important; color: white !important; }
    h1, h2 { color: #005596; border-bottom: 2px solid #5c2d91; }
    .pop-section { background-color: #ffffff; padding: 15px; border-left: 5px solid #005596; border-radius: 0 0 8px 8px; overflow-x: auto; }
    .stExpander { border: 1px solid #e6e6e6; margin-bottom: 5px; border-radius: 8px !important; }
    /* Estilo para Tabelas Extraídas */
    table { width: 100%; border-collapse: collapse; margin: 10px 0; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background-color: #005596; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 2. FUNÇÃO: EXTRAÇÃO DE TEXTO E TABELAS
def display_smart_pdf_with_tables(file_path):
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                # Extrai o texto da página
                text = page.extract_text()
                if text:
                    # Identifica tópicos (Ex: 1. OBJETIVO)
                    parts = re.split(r'(\d+\.\s+[A-ZÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇ\s]{3,})', text)
                    
                    if len(parts) > 1:
                        for i in range(1, len(parts), 2):
                            titulo = parts[i].strip()
                            conteudo = parts[i+1].strip() if (i+1) < len(parts) else ""
                            with st.expander(f"🔹 {titulo}"):
                                st.markdown(f'<div class="pop-section">{conteudo}</div>', unsafe_allow_html=True)
                                
                                # Verifica se há tabelas NESTA página para este tópico
                                tables = page.extract_tables()
                                for table in tables:
                                    st.write("📊 **Tabela de Dados:**")
                                    st.table(table)
                    else:
                        # Se não houver tópicos claros, tenta mostrar a tabela direto
                        st.write(text)
                        tables = page.extract_tables()
                        for table in tables:
                            st.table(table)
    except Exception as e:
        st.error(f"Erro ao processar tabelas do PDF: {e}")

# --- (As funções de Feed, Login e Busca permanecem as mesmas abaixo) ---

FEED_FILE = "feed_data.json"
def carregar_feed():
    if os.path.exists(FEED_FILE):
        with open(FEED_FILE, "r") as f: return json.load(f)
    return []

def salvar_feed_completo(feed):
    with open(FEED_FILE, "w") as f: json.dump(feed, f)

def adicionar_post(mensagem, imagem=None):
    feed = carregar_feed()
    novo_post = {"id": datetime.now().strftime("%Y%m%d%H%M%S"), "data": datetime.now().strftime("%d/%m/%Y %H:%M"), "msg": mensagem, "img": imagem, "curtidas": 0, "comentarios": []}
    feed.insert(0, novo_post)
    salvar_feed_completo(feed[:30])

def buscar_nos_arquivos(termo, pasta):
    res = []
    termo = termo.lower().strip()
    arqs = sorted([f for f in os.listdir(pasta) if f.lower().endswith('.pdf')])
    for a in arqs:
        match = False
        if termo in a.lower(): match = True
        if not match:
            try:
                with pdfplumber.open(os.path.join(pasta, a)) as p:
                    for page in p.pages:
                        if termo in page.extract_text().lower(): match = True; break
            except: pass
        if match: res.append(a)
    return res

# --- INTERFACE ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.image("https://www.mideacarrier.com.br/wp-content/themes/midea-carrier/assets/img/logo-midea-carrier.png", width=250)
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("ACESSAR"):
            users = st.secrets.get("passwords", {"admin": "midea123", "treinamento": "midea_treina"})
            if u in users and str(users[u]) == p:
                st.session_state.autenticado, st.session_state.user_logado = True, u
                st.rerun()
            else: st.error("Erro no login.")
    st.stop()

st.sidebar.image("https://www.mideacarrier.com.br/wp-content/themes/midea-carrier/assets/img/logo-midea-carrier.png", width=130)
menu = st.sidebar.radio("Navegação", ["📢 Feed", "📚 Wiki POPs", "⚙️ Gestão"])

if menu == "📢 Feed":
    st.title("📢 Feed da Operação")
    feed = carregar_feed()
    for i, post in enumerate(feed):
        with st.chat_message("user", avatar="❄️"):
            c_txt, c_del = st.columns([0.85, 0.15])
            with c_txt:
                st.write(f"**[{post['data']}]** - {post['msg']}")
                if post.get('img'): st.image(post['img'])
            if st.session_state.user_logado in ["admin", "treinamento"]:
                with c_del:
                    if st.button("🗑️", key=f"del_{post['id']}"):
                        feed.pop(i); salvar_feed_completo(feed); st.rerun()
            
            # Curtidas/Comentários
            col_lk, _ = st.columns([0.2, 0.8])
            if col_lk.button(f"❤️ {post['curtidas']}", key=f"lk_{post['id']}"):
                feed[i]['curtidas'] += 1; salvar_feed_completo(feed); st.rerun()
            
            with st.expander(f"💬 Comentários ({len(post['comentarios'])})"):
                for c in post['comentarios']: st.info(f"**{c['user']}:** {c['txt']}")
                nc = st.text_input("Comentar...", key=f"in_{post['id']}")
                if st.button("Postar", key=f"bt_{post['id']}"):
                    feed[i]['comentarios'].append({"user": st.session_state.user_logado, "txt": nc})
                    salvar_feed_completo(feed); st.rerun()

elif menu == "📚 Wiki POPs":
    st.title("📚 Wiki")
    busca = st.text_input("🔍 Buscar...")
    pasta = "documentos"
    if not os.path.exists(pasta): os.makedirs(pasta)
    arqs = buscar_nos_arquivos(busca, pasta) if busca else sorted([f for f in os.listdir(pasta) if f.lower().endswith('.pdf')])
    for a in arqs:
        with st.expander(f"📂 {a.replace('.pdf', '')}"):
            t1, t2 = st.tabs(["📖 Ver Conteúdo", "📥 Download"])
            with t1: display_smart_pdf_with_tables(os.path.join(pasta, a))
            with t2: st.download_button("Baixar PDF", open(os.path.join(pasta, a), "rb"), file_name=a)

elif menu == "⚙️ Gestão":
    if st.session_state.user_logado in ["admin", "treinamento"]:
        st.title("⚙️ Painel Gestor")
        up = st.file_uploader("Subir POP (PDF)", type=['pdf'])
        if up:
            with open(os.path.join("documentos", up.name), "wb") as f: f.write(up.getbuffer())
            adicionar_post(f"✅ NOVO POP: {up.name} (Por {st.session_state.user_logado})")
            st.success("Salvo!"); st.rerun()
        
        st.divider()
        m = st.text_area("Novo Post no Feed")
        i_up = st.file_uploader("Anexar Imagem", type=['png', 'jpg'])
        if st.button("Publicar Comunicado"):
            img = f"data:image/png;base64,{base64.b64encode(i_up.read()).decode()}" if i_up else None
            adicionar_post(f"📣 {m} (TL: {st.session_state.user_logado})", img)
            st.success("Postado!"); st.rerun()
