import streamlit as st
import os
import pandas as pd
from PyPDF2 import PdfReader

# 1. CONFIGURAÇÃO DE IDENTIDADE VISUAL MIDEA CARRIER
st.set_page_config(page_title="Base de Conhecimento Midea", layout="wide", page_icon="❄️")

# CSS para cores corporativas (Azul Midea #005596)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { background-color: #005596; color: white; border: none; padding: 10px 20px; border-radius: 5px; }
    .stTextInput>div>div>input { border-color: #005596; }
    h1, h2, h3 { color: #005596; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #e9ecef; 
        border-radius: 4px 4px 0px 0px; 
        padding: 10px 20px;
        color: #495057;
    }
    .stTabs [aria-selected="true"] { background-color: #005596 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. GESTÃO DE USUÁRIOS VIA STREAMLIT SECRETS
# No Streamlit Cloud, vá em Settings > Secrets e adicione:
# [passwords]
# admin = "sua_senha"
# operador = "outra_senha"

def verificar_login():
    if "passwords" in st.secrets:
        usuarios = st.secrets["passwords"]
    else:
        # Usuário padrão caso os Secrets não estejam configurados ainda
        usuarios = {"admin": "midea2026"}

    st.sidebar.image("https://www.mideacarrier.com.br/wp-content/themes/midea-carrier/assets/img/logo-midea-carrier.png", width=150)
    st.sidebar.title("Acesso Restrito")
    
    user = st.sidebar.text_input("Usuário", key="user_input")
    pw = st.sidebar.text_input("Senha", type="password", key="pw_input")
    
    if user in usuarios and str(usuarios[user]) == pw:
        return True, user
    elif user:
        st.sidebar.error("Credenciais inválidas.")
    return False, None

autenticado, user_logado = verificar_login()

if autenticado:
    st.title("❄️ Portal de Conhecimento - Operação Midea Carrier")
    
    # 3. FEED DE COMUNICADOS (Área de Avisos)
    st.subheader("📢 Feed de Atualizações")
    # Dica: Você pode transformar isso em um arquivo .txt no GitHub para atualizar remotamente
    with st.container():
        st.info("**Aviso:** Atualização nos protocolos de atendimento Blue Service disponível abaixo.")
        st.caption("Postado em: 25/03/2026")

    st.divider()

    # 4. SISTEMA DE BUSCA (Título e Conteúdo do Texto)
    col1, col2 = st.columns([2, 1])
    with col1:
        busca = st.text_input("🔍 O que você procura? (Busca em títulos e dentro dos arquivos)", placeholder="Ex: Ar condicionado, Garantia, iService...")

    # 5. GERENCIAMENTO DE ARQUIVOS
    pasta_docs = "documentos"
    if not os.path.exists(pasta_docs):
        os.makedirs(pasta_docs)

    arquivos = sorted([f for f in os.listdir(pasta_docs) if not f.startswith('.')])

    if arquivos:
        st.write(f"Exibindo {len(arquivos)} documentos disponíveis:")
        
        # Criação automática de abas baseada nos arquivos
        tabs = st.tabs([f"📄 {arq.replace('.pdf', '').replace('.docx', '')}" for arq in arquivos])
        
        for i, arq in enumerate(arquivos):
            caminho = os.path.join(pasta_docs, arq)
            encontrado_no_texto = False
            conteudo_preview = ""

            # Lógica de Busca dentro de PDF
            if busca and arq.lower().endswith('.pdf'):
                try:
                    reader = PdfReader(caminho)
                    texto_completo = ""
                    for page in reader.pages:
                        texto_completo += page.extract_text()
                    
                    if busca.lower() in texto_completo.lower():
                        encontrado_no_texto = True
                except Exception as e:
                    pass

            with tabs[i]:
                # Destaque se a busca bater com o título ou conteúdo
                if busca:
                    if busca.lower() in arq.lower() or encontrado_no_texto:
                        st.success(f"🎯 Termo '{busca}' localizado neste documento!")
                    else:
                        st.warning("Termo não encontrado neste item.")

                st.write(f"**Nome Técnico:** {arq}")
                
                with open(caminho, "rb") as f:
                    st.download_button(
                        label=f"📥 Baixar {arq}",
                        data=f,
                        file_name=arq,
                        mime="application/octet-stream",
                        key=f"btn_{i}"
                    )

    # 6. PAINEL DO TEAM LEADER (ADMIN)
    if user_logado == "admin":
        st.sidebar.divider()
        st.sidebar.subheader("⚙️ Painel de Gestão (TL)")
        
        upload = st.sidebar.file_uploader("Atualizar/Subir POP", type=['pdf', 'docx'])
        
        if upload:
            # Lógica de substituição automática
            # Se subir "Manual.pdf" e já existir "Manual.pdf", o novo sobrescreve o antigo no Python
            caminho_novo = os.path.join(pasta_docs, upload.name)
            
            with open(caminho_novo, "wb") as f:
                f.write(upload.getbuffer())
            
            st.sidebar.success(f"Arquivo '{upload.name}' atualizado com sucesso!")
            st.rerun()

        # Botão para limpar busca
        if st.sidebar.button("Limpar Filtros"):
            st.rerun()

else:
    st.info("Aguardando login para liberar acesso à base de conhecimento da Concentrix / Midea.")
    st.image("https://www.midea.com/content/dam/midea-aem/br/midea-carrier/sobre-nos/banner-sobre-nos-desktop.jpg")
