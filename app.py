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
    .btn-excluir>div>button { background: #d9534f !important; color: white !important; border-radius: 5px; }
    h1, h2 { color: #005596; border-bottom: 2px solid #5c2d91; }
    .pop-section { background-color: #ffffff; padding: 15px; border-left: 5px solid #005596; color: #333; border-radius: 0 0 8px 8px; }
    .stExpander { border: 1px solid #e6e6e6; margin-bottom: 5px; border-radius: 8px !important; }
    .comment-box { background-color: #f8f9fa; padding: 8px; border-radius: 5px; margin-top: 5px; border-left: 3px solid #5c2d91; font-size: 0.9em; }
    </style>
    """, unsafe_allow_html=True)

# 2. GESTÃO DO FEED (Persistência com Curtidas e Comentários)
FEED_FILE = "feed_data.json"

def carregar_feed():
    if os.path.exists(FEED_FILE):
        with open(FEED_FILE, "r") as f:
            return json.load(f)
    return []

def salvar_feed_completo(feed):
    with open(FEED_FILE, "w") as f:
        json.dump(feed, f)

def adicionar_post(mensagem, imagem_base64=None):
    feed = carregar_feed()
    novo_post = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "msg": mensagem,
        "img": imagem_base64,
        "curtidas": 0,
        "comentarios": []
    }
    feed.insert(0, novo_post)
    salvar_feed_completo(feed[:30]) # Mantém os últimos 30 avisos

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
            # O sistema busca nos Secrets. Cadastre usuários como joao_admin ou paulo_treina lá.
            usuarios = st.secrets.get("passwords", {"admin": "midea123"})
            if user in usuarios and str(usuarios[user]) == pw:
                st.session_state.autenticado = True
                st.session_state.user_logado = user
                st.rerun()
            else: st.error("Usuário ou senha inválidos.")
    st.stop()

# Lógica de permissão por sufixo
e_gestor = "_admin" in st.session_state.user_logado or "_treina" in st.session_state.user_logado

# 5. MENU E NAVEGAÇÃO
st.sidebar.image("https://www.mideacarrier.com.br/wp-content/themes/midea-carrier/assets/img/logo-midea-carrier.png", width=130)
st.sidebar.markdown(f"👤 **Logado:** `{st.session_state.user_logado}`")

opcoes = ["📢 Feed da Operação", "📚 Wiki POPs"]
if e_gestor:
    opcoes.append("⚙️ Gestão (TL/Treinamento)")

menu = st.sidebar.radio("Navegação", opcoes)

if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()

# --- TELA: FEED ---
if menu == "📢 Feed da Operação":
    st.title("📢 Comunicados e Avisos")
    feed = carregar_feed()
    
    if not feed:
        st.info("Nenhum comunicado no momento.")
    
    for i, post in enumerate(feed):
        with st.chat_message("user", avatar="❄️"):
            col_txt, col_del = st.columns([0.9, 0.1])
            with col_txt:
                st.write(f"**[{post['data']}]**")
                st.write(post['msg'])
            
            # Botão de Excluir (Apenas para Gestores)
            if e_gestor:
                with col_del:
                    st.markdown('<div class="btn-excluir">', unsafe_allow_html=True)
                    if st.button("🗑️", key=f"del_{post['id']}"):
                        feed.pop(i)
                        salvar_feed_completo(feed)
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

            if post.get('img'):
                st.image(post['img'], use_column_width=True)
            
            # Interação: Curtidas
            col_like, _ = st.columns([0.15, 0.85])
            if col_like.button(f"❤️ {post['curtidas']}", key=f"like_{post['id']}"):
                feed[i]['curtidas'] += 1
                salvar_feed_completo(feed)
                st.rerun()
            
            # Interação: Comentários
            with st.expander(f"💬 Comentários ({len(post['comentarios'])})"):
                for c in post['comentarios']:
                    st.markdown(f'<div class="comment-box"><b>{c["user"]}:</b> {c["txt"]}</div>', unsafe_allow_html=True)
                
                new_comm = st.text_input("Adicionar comentário...", key=f"in_{post['id']}")
                if st.button("Enviar", key=f"btn_{post['id']}"):
                    if new_comm:
                        feed[i]['comentarios'].append({"user": st.session_state.user_logado, "txt": new_comm})
                        salvar_feed_completo(feed)
                        st.rerun()

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
            with st.expander(f"📂 {arq.replace('.pdf', '')}", expanded=bool(busca)):
                tab_ler, tab_dl = st.tabs(["📖 Ver Conteúdo", "📥 Download"])
                with tab_ler: display_smart_pdf(os.path.join(pasta, arq))
                with tab_dl:
                    with open(os.path.join(pasta, arq), "rb") as f:
                        st.download_button(f"Baixar {arq}", f, file_name=arq, key=f"dl_{arq}")

# --- TELA: GESTÃO ---
elif menu == "⚙️ Gestão (TL/Treinamento)":
    if e_gestor:
        st.title("⚙️ Painel de Gestão")
        
        # 1. Atualizar POP
        st.subheader("1. Atualizar/Subir POP")
        upload_pop = st.file_uploader("Selecione o PDF", type=['pdf'], key="pop_up")
        if upload_pop:
            if not os.path.exists("documentos"): os.makedirs("documentos")
            with open(os.path.join("documentos", upload_pop.name), "wb") as f:
                f.write(upload_pop.getbuffer())
            adicionar_post(f"✅ NOVO POP: O arquivo '{upload_pop.name}' foi atualizado na Wiki por {st.session_state.user_logado}.")
            st.success("POP atualizado e notificado no Feed!")
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
                adicionar_post(f"📣 {aviso_msg} (Por: {st.session_state.user_logado})", img_b64)
                st.success("Comunicado publicado!")
                st.rerun()
    else:
        st.error("Acesso negado. Apenas usuários Admin ou Treinamento podem acessar esta aba.")
