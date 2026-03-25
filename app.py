import streamlit as st
import os
import pandas as pd
from PyPDF2 import PdfReader

# Configuração de Identidade Visual Midea/Concentrix
st.set_page_config(page_title="Portal de Conhecimento Midea", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { background-color: #005596; color: white; border-radius: 5px; }
    .stTextInput>div>div>input { border-color: #005596; }
    h1 { color: #005596; font-family: 'Arial'; }
    </style>
    """, unsafe_allow_html=True)

# 1. GESTÃO DE USUÁRIOS (Simples para início)
usuarios = {"admin": "midea123", "operador": "concentrix2024"}

def login():
    st.sidebar.title("Canais de Acesso")
    user = st.sidebar.text_input("Usuário")
    pw = st.sidebar.text_input("Senha", type="password")
    if user in usuarios and usuarios[user] == pw:
        return True, user
    return False, None

autenticado, user_logado = login()

if autenticado:
    st.title("❄️ Portal de Conhecimento - Operação Midea Carrier")
    
    # 2. ÁREA DE COMUNICADOS (FEED)
    st.subheader("📢 Comunicados e Atualizações")
    with st.expander("Ver Feed de Notícias", expanded=True):
        st.info("⚠️ **IMPORTANTE:** Novo fluxo de atendimento Blue Service atualizado em 13/03.")
        st.warning("🛠️ Manutenção no sistema iService agendada para as 22h.")

    # 3. BUSCA AVANÇADA (Título e Conteúdo)
    st.divider()
    busca = st.text_input("🔍 O que você deseja encontrar hoje? (Busca em PDF e Títulos)")
    
    pasta_docs = "documentos"
    if not os.path.exists(pasta_docs): os.makedirs(pasta_docs)

    arquivos = os.listdir(pasta_docs)
    
    # 4. EXIBIÇÃO EM ABAS POR ITEM
    if arquivos:
        tabs = st.tabs([f"📄 {arq.split('.')[0]}" for arq in arquivos])
        
        for i, arq in enumerate(arquivos):
            caminho = os.path.join(pasta_docs, arq)
            with tabs[i]:
                st.write(f"**Nome do Arquivo:** {arq}")
                # Lógica de leitura de texto para busca
                if busca:
                    try:
                        reader = PdfReader(caminho)
                        texto_completo = " ".join([page.extract_text() for page in reader.pages])
                        if busca.lower() in texto_completo.lower() or busca.lower() in arq.lower():
                            st.success("✅ Termo encontrado neste documento!")
                    except: pass
                
                with open(caminho, "rb") as f:
                    st.download_button("Baixar POP/Arquivo", f, file_name=arq)

    # 5. ÁREA ADMIN: UPLOAD E EXCLUSÃO AUTOMÁTICA
    if user_logado == "admin":
        st.sidebar.divider()
        st.sidebar.subheader("⚙️ Painel do Team Leader")
        novo_arquivo = st.sidebar.file_uploader("Subir novo POP (Substitui antigo)", type=['pdf', 'docx'])
        
        if novo_arquivo:
            # Lógica de exclusão automática: se o nome base existir, apaga o antigo
            for arq_existente in os.listdir(pasta_docs):
                if arq_existente.split('.')[0] == novo_arquivo.name.split('.')[0]:
                    os.remove(os.path.join(pasta_docs, arq_existente))
            
            with open(os.path.join(pasta_docs, novo_arquivo.name), "wb") as f:
                f.write(novo_arquivo.getbuffer())
            st.sidebar.success("Arquivo atualizado e antigo removido!")
            st.rerun()
else:
    st.error("Por favor, faça o login para acessar a base Midea.")
