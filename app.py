import streamlit as st
import os
import base64
from PyPDF2 import PdfReader

# 1. CONFIGURAÇÃO DE IDENTIDADE VISUAL HÍBRIDA (MIDEA + CONCENTRIX)
st.set_page_config(page_title="Portal Midea | Concentrix", layout="wide", page_icon="❄️")

st.markdown("""
    <style>
    /* Cores Principais */
    :root {
        --midea-blue: #005596;
        --concentrix-purple: #5c2d91;
    }
    .main { background-color: #f4f7f9; }
    
    /* Botões com degradê Midea/Concentrix */
    .stButton>button { 
        background: linear-gradient(90deg, #005596 0%, #5c2d91 100%); 
        color: white; border: none; font-weight: bold; border-radius: 8px;
    }
    
    /* Títulos e Cabeçalhos */
    h1, h2 { color: #005596; font-family: 'Arial'; }
    h3 { color: #5c2d91; }

    /* Customização das Abas (Tabs) */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border: 1px solid #ddd;
        border-radius: 5px 5px 0 0;
        padding: 8px 15px;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #005596 !important; 
        color: white !important; 
        border: 1px solid #005596 !important;
    }

    /* Estilo do Iframe do PDF */
    .pdf-frame { border: 3px solid #005596; border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

# 2. FUNÇÕES DE APOIO
def display_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="700" type="application/pdf" class="pdf-frame"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# 3. SISTEMA DE LOGIN
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.image("https://www.mideacarrier.com.br/wp-content/themes/midea-carrier/assets/img/logo-midea-carrier.png", width=250)
        st.write("---")
        st.subheader("🔐 Acesso Restrito à Operação")
        user = st.text_input("Usuário Concentrix / Midea")
        pw = st.text_input("Senha", type="password")
        if st.button("ACESSAR PORTAL"):
            usuarios = st.secrets.get("passwords", {"admin": "midea123"})
            if user in usuarios and str(usuarios[user]) == pw:
                st.session_state.autenticado = True
                st.session_state.user_logado = user
                st.rerun()
            else:
                st.error("Erro: Usuário ou senha inválidos.")
    st.stop()

# 4. DASHBOARD PRINCIPAL (PÓS-LOGIN)
st.sidebar.image("https://www.mideacarrier.com.br/wp-content/themes/midea-carrier/assets/img/logo-midea-carrier.png", width=150)
st.sidebar.markdown(f"**Usuário:** `{st.session_state.user_logado}`")
menu = st.sidebar.radio("Menu Principal", ["📢 Feed de Notícias", "📚 Wiki de Processos", "⚙️ Painel Admin"])

if st.sidebar.button("Sair do Sistema"):
    st.session_state.autenticado = False
    st.rerun()

# --- TELA: FEED ---
if menu == "📢 Feed de Notícias":
    st.title("📢 Feed da Operação")
    st.markdown("### Informativos Recentes")
    
    with st.chat_message("user", avatar="❄️"):
        st.write("**⚠️ ATUALIZAÇÃO BLUE SERVICE (13/03)**")
        st.write("O formato de atendimento para climatizadores agora aceita In-Home e Carry-In. Verifique o manual na Wiki.")
    
    with st.chat_message("user", avatar="🟣"):
        st.write("**⚙️ STATUS ISERVICE**")
        st.write("Sistema operando normalmente. Backlog de tickets em queda.")

# --- TELA: WIKI (COM BUSCA E VISUALIZAÇÃO) ---
elif menu == "📚 Wiki de Processos":
    st.title("📚 Wiki de Conhecimento")
    busca = st.text_input("🔍 Pesquisar em Títulos e Conteúdo dos POPs", placeholder="Ex: Climatizador, Garantia...")
    
    pasta = "documentos"
    arquivos = sorted([f for f in os.listdir(pasta) if not f.startswith('.')])

    if arquivos:
        for arq in arquivos:
            caminho = os.path.join(pasta, arq)
            
            # Lógica de expansão automática na busca
            expandir = False
            if busca:
                if busca.lower() in arq.lower():
                    expandir = True
                elif arq.lower().endswith('.pdf'):
                    try:
                        reader = PdfReader(caminho)
                        for page in reader.pages:
                            if busca.lower() in page.extract_text().lower():
                                expandir = True
                                break
                    except: pass

            # ESTRUTURA DE ABAS RECOLHIDAS (EXPANDERS)
            with st.expander(f"📂 {arq.replace('.pdf', '')}", expanded=expandir):
                # ABAS INTERNAS PARA CADA ITEM
                tab_doc, tab_info = st.tabs(["📄 Visualizar Documento", "ℹ️ Detalhes e Download"])
                
                with tab_doc:
                    if arq.lower().endswith('.pdf'):
                        display_pdf(caminho)
                    else:
                        st.info("Visualização rápida disponível apenas para PDFs.")

                with tab_info:
                    st.write(f"**Nome do Arquivo:** {arq}")
                    st.write("**Operação:** Midea Carrier / Concentrix")
                    with open(caminho, "rb") as f:
                        st.download_button(f"📥 Baixar Arquivo Original", f, file_name=arq, key=f"dl_{arq}")
    else:
        st.warning("Nenhum documento encontrado na pasta /documentos.")

# --- TELA: ADMIN ---
elif menu == "⚙️ Painel Admin":
    if st.session_state.user_logado == "admin":
        st.title("⚙️ Painel do Team Leader")
        st.info("Dica: Ao subir um arquivo com o mesmo nome, o antigo é excluído automaticamente.")
        
        upload = st.file_uploader("Upload de novo POP", type=['pdf', 'docx'])
        if upload:
            with open(os.path.join("documentos", upload.name), "wb") as f:
                f.write(upload.getbuffer())
            st.success("Arquivo atualizado com sucesso na base!")
            st.balloons()
    else:
        st.error("Acesso negado. Apenas administradores podem gerenciar arquivos.")
