import streamlit as st
import os
import re
from PyPDF2 import PdfReader

# 1. CONFIGURAÇÃO VISUAL HÍBRIDA
st.set_page_config(page_title="Portal Midea | Concentrix", layout="wide", page_icon="❄️")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    .stButton>button { 
        background: linear-gradient(90deg, #005596 0%, #5c2d91 100%); 
        color: white; border: none; font-weight: bold; border-radius: 8px; width: 100%;
    }
    h1, h2 { color: #005596; font-family: 'Arial'; border-bottom: 2px solid #5c2d91; padding-bottom: 10px; }
    .pop-section {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 0px 0px 8px 8px;
        border-left: 5px solid #005596;
        line-height: 1.6;
        color: #333;
    }
    /* Estilo para os sub-menus internos */
    .stExpander { border: 1px solid #e6e6e6; margin-bottom: 5px; border-radius: 8px !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. FUNÇÃO: IDENTIFICA TÓPICOS E CRIA MENUS AUTOMÁTICOS
def display_smart_pdf(file_path):
    try:
        reader = PdfReader(file_path)
        texto_completo = ""
        for page in reader.pages:
            texto_completo += page.extract_text() + "\n"

        # Regex para identificar padrões como "1. OBJETIVO", "2. PROCEDIMENTO", "3. CONCLUSÃO"
        # Ele busca números seguidos de ponto e palavras em maiúsculo
        topicos = re.split(r'(\n\d+\.\s+[A-ZÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇ\s]+)', texto_completo)
        
        if len(topicos) <= 1:
            # Se não encontrar números, exibe o texto normal
            st.markdown(f'<div class="pop-section">{texto_completo}</div>', unsafe_allow_html=True)
        else:
            # O primeiro item costuma ser o cabeçalho antes do item 1
            if topicos[0].strip():
                st.write(topicos[0])
            
            # Percorre os tópicos encontrados (Tópico, Conteúdo, Tópico, Conteúdo...)
            for i in range(1, len(topicos), 2):
                titulo_topico = topicos[i].strip()
                conteudo_topico = topicos[i+1].strip() if (i+1) < len(topicos) else ""
                
                # CRIA O MENU SUSPENSO AUTOMÁTICO PARA CADA ITEM
                with st.expander(f"🔹 {titulo_topico}"):
                    st.markdown(f'<div class="pop-section">{conteudo_topico}</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Erro ao processar tópicos: {e}")

# 3. SISTEMA DE LOGIN
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.image("https://www.mideacarrier.com.br/wp-content/themes/midea-carrier/assets/img/logo-midea-carrier.png", width=250)
        st.write("---")
        st.subheader("❄️ Acesso à Base de Conhecimento")
        user = st.text_input("Usuário (ID Concentrix/Midea)")
        pw = st.text_input("Senha", type="password")
        if st.button("ENTRAR NO PORTAL"):
            usuarios = st.secrets.get("passwords", {"admin": "midea123"})
            if user in usuarios and str(usuarios[user]) == pw:
                st.session_state.autenticado = True
                st.session_state.user_logado = user
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
    st.stop()

# 4. INTERFACE PRINCIPAL
st.sidebar.image("https://www.mideacarrier.com.br/wp-content/themes/midea-carrier/assets/img/logo-midea-carrier.png", width=140)
st.sidebar.markdown(f"👤 **Logado como:** `{st.session_state.user_logado}`")
menu = st.sidebar.radio("Navegação", ["📢 Feed", "📚 Wiki POPs", "⚙️ Gestão TL"])

if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()

# --- TELA: WIKI POPs ---
if menu == "📚 Wiki POPs":
    st.title("📚 Wiki de Conhecimento")
    busca = st.text_input("🔍 Pesquisar POP (Título ou Conteúdo)")
    
    pasta = "documentos"
    if not os.path.exists(pasta): os.makedirs(pasta)
    arquivos = sorted([f for f in os.listdir(pasta) if not f.startswith('.')])

    for arq in arquivos:
        caminho = os.path.join(pasta, arq)
        
        # O "Menu Principal" do POP que você mencionou
        with st.expander(f"📂 {arq.replace('.pdf', '')}", expanded=bool(busca and busca.lower() in arq.lower())):
            tab_ler, tab_download = st.tabs(["📖 Visualizar Processo", "📥 Download"])
            
            with tab_ler:
                if arq.lower().endswith('.pdf'):
                    # CHAMA A FUNÇÃO QUE CRIA OS SUB-MENUS AUTOMÁTICOS (1. OBJETIVO, etc)
                    display_smart_pdf(caminho)
                else:
                    st.info("Visualização automática disponível para PDFs.")

            with tab_download:
                with open(caminho, "rb") as f:
                    st.download_button(f"📥 Baixar {arq}", f, file_name=arq, key=f"dl_{arq}")

# --- TELA: FEED ---
elif menu == "📢 Feed":
    st.title("📢 Feed da Operação")
    st.info("**⚠️ NOVO PROCEDIMENTO:** O POP de E-ticket foi atualizado com as novas regras de sinistro.")

# --- TELA: GESTÃO ---
elif menu == "⚙️ Gestão TL":
    if st.session_state.user_logado == "admin":
        st.title("⚙️ Painel do Team Leader")
        upload = st.file_uploader("Subir Novo POP", type=['pdf'])
        if upload:
            with open(os.path.join("documentos", upload.name), "wb") as f:
                f.write(upload.getbuffer())
            st.success("Base atualizada!")
    else:
        st.error("Acesso restrito.")
