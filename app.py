import streamlit as st
import os
import base64
from PyPDF2 import PdfReader

# 1. CONFIGURAÇÃO DE IDENTIDADE VISUAL (MIDEA #005596 + CONCENTRIX #5c2d91)
st.set_page_config(page_title="Portal Midea | Concentrix", layout="wide", page_icon="❄️")

st.markdown("""
    <style>
    /* Estilização Geral */
    .main { background-color: #f4f7f9; }
    
    /* Botões com degradê corporativo */
    .stButton>button { 
        background: linear-gradient(90deg, #005596 0%, #5c2d91 100%); 
        color: white; border: none; font-weight: bold; border-radius: 8px; width: 100%;
    }
    
    /* Títulos */
    h1, h2 { color: #005596; font-family: 'Arial'; border-bottom: 2px solid #5c2d91; padding-bottom: 10px; }
    h3 { color: #5c2d91; }

    /* Customização das Abas internas da Wiki */
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
    }

    /* Caixa de Texto do POP Incorporado */
    .pop-container {
        background-color: white; 
        padding: 25px; 
        border-left: 8px solid #005596; 
        border-radius: 8px; 
        height: 600px; 
        overflow-y: scroll; 
        white-space: pre-wrap;
        font-family: 'Segoe UI', sans-serif; 
        color: #333; 
        line-height: 1.8;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# 2. FUNÇÃO: INCORPORAR TEXTO DO PDF NO SITE
def display_pdf_as_text(file_path):
    try:
        reader = PdfReader(file_path)
        texto_extraido = ""
        for page in reader.pages:
            texto_extraido += page.extract_text() + "\n" + "-"*50 + "\n"
        
        # HTML para a caixa de texto com rolagem
        st.markdown(f'<div class="pop-container">{texto_extraido}</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erro ao processar o conteúdo do PDF: {e}")

# 3. SISTEMA DE SESSÃO E LOGIN
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
            # Tenta ler dos Secrets, se não houver, usa o padrão admin/midea123
            usuarios = st.secrets.get("passwords", {"admin": "midea123"})
            if user in usuarios and str(usuarios[user]) == pw:
                st.session_state.autenticado = True
                st.session_state.user_logado = user
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
    st.stop()

# 4. INTERFACE PRINCIPAL (PÓS-LOGIN)
st.sidebar.image("https://www.mideacarrier.com.br/wp-content/themes/midea-carrier/assets/img/logo-midea-carrier.png", width=140)
st.sidebar.markdown(f"👤 **Logado como:** `{st.session_state.user_logado}`")
st.sidebar.divider()

menu = st.sidebar.radio("Navegação Principal", ["📢 Feed da Operação", "📚 Wiki de Processos (POPs)", "⚙️ Área do Gestor (TL)"])

if st.sidebar.button("Logoff / Sair"):
    st.session_state.autenticado = False
    st.rerun()

# --- TELA 1: FEED ---
if menu == "📢 Feed da Operação":
    st.title("📢 Feed de Comunicados")
    st.markdown("### Atualizações e Notificações Importantes")
    
    st.info("**⚠️ AVISO BLUE SERVICE (Março/2026):** Verifique o novo fluxo de abertura de e-tickets para climatizadores na Wiki.")
    
    with st.expander("Ver histórico de comunicados", expanded=True):
        st.write("- **13/03:** Alteração no formato de atendimento (In-Home e Carry-In).")
        st.write("- **10/03:** Treinamento iService disponível na plataforma de E-learning.")
    
    st.success("✅ Sistema iService operando sem instabilidades no momento.")

# --- TELA 2: WIKI (INCORPORADA) ---
elif menu == "📚 Wiki de Processos (POPs)":
    st.title("📚 Wiki de Conhecimento")
    busca = st.text_input("🔍 Pesquisar em títulos ou dentro dos textos", placeholder="Digite o que procura...")
    
    pasta = "documentos"
    if not os.path.exists(pasta): os.makedirs(pasta)
    
    arquivos = sorted([f for f in os.listdir(pasta) if not f.startswith('.')])

    if arquivos:
        for arq in arquivos:
            caminho = os.path.join(pasta, arq)
            
            # Lógica para expandir automaticamente se a busca bater
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

            # ESTRUTURA RECOLHIDA (SUSPENSA)
            with st.expander(f"📂 {arq.replace('.pdf', '').replace('.docx', '')}", expanded=expandir):
                tab_ler, tab_download = st.tabs(["📖 Ler no Site", "📥 Info e Download"])
                
                with tab_ler:
                    if arq.lower().endswith('.pdf'):
                        st.markdown(f"#### Conteúdo extraído: {arq}")
                        display_pdf_as_text(caminho)
                    else:
                        st.warning("Visualização direta disponível para PDFs. Use a aba ao lado para baixar outros formatos.")

                with tab_download:
                    st.write(f"**Documento:** {arq}")
                    st.write("**Operação:** Midea Carrier / Concentrix")
                    with open(caminho, "rb") as f:
                        st.download_button(f"📥 Baixar Arquivo Original", f, file_name=arq, key=f"dl_{arq}")
    else:
        st.warning("Nenhum arquivo encontrado na pasta /documentos. Suba um novo no painel de gestão.")

# --- TELA 3: ADMIN ---
elif menu == "⚙️ Área do Gestor (TL)":
    if st.session_state.user_logado == "admin":
        st.title("⚙️ Painel de Gestão (Team Leader)")
        st.subheader("Atualização da Base de Conhecimento")
        
        st.warning("Ao realizar o upload de um arquivo com o MESMO NOME de um já existente, o sistema substituirá o antigo automaticamente.")
        
        upload = st.file_uploader("Selecione o novo POP (PDF ou DOCX)", type=['pdf', 'docx'])
        if upload:
            with open(os.path.join("documentos", upload.name), "wb") as f:
                f.write(upload.getbuffer())
            st.success(f"O documento '{upload.name}' foi atualizado com sucesso!")
            st.balloons()
    else:
        st.error("Acesso negado. Esta área é restrita aos administradores/TLs.")
