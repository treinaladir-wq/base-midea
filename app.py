import streamlit as st
import os
import json
import base64
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO VISUAL
st.set_page_config(page_title="Midea | Formação Continuada", layout="wide", page_icon="🎓")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    .stButton>button { 
        background: linear-gradient(90deg, #005596 0%, #5c2d91 100%); 
        color: white; border: none; font-weight: bold; border-radius: 8px;
    }
    .stExpander { border: 1px solid #e6e6e6; border-radius: 8px !important; margin-bottom: 10px; }
    h1, h2, h3 { color: #005596; }
    .nota-alta { color: #28a745; font-weight: bold; }
    .nota-baixa { color: #d9534f; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. PERSISTÊNCIA DE DADOS
FEED_FILE = "feed_data.json"
TREINAMENTOS_FILE = "treinamentos.json"
NOTAS_FILE = "notas_provas.json"

def carregar_dados(arquivo):
    if os.path.exists(arquivo):
        with open(arquivo, "r") as f: return json.load(f)
    return []

def salvar_dados(dados, arquivo):
    with open(arquivo, "w") as f: json.dump(dados, f)

# 3. CONTROLE DE ACESSO
if 'autenticado' not in st.session_state: st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.image("https://www.mideacarrier.com.br/wp-content/themes/midea-carrier/assets/img/logo-midea-carrier.png", width=250)
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("ENTRAR"):
            users = st.secrets.get("passwords", {"admin": "midea123"})
            if u in users and str(users[u]) == p:
                st.session_state.autenticado, st.session_state.user_logado = True, u
                st.rerun()
            else: st.error("Acesso negado.")
    st.stop()

# Identificação de permissão por sufixo (conforme solicitado para Admin e Treinamento)
e_gestor = "_admin" in st.session_state.user_logado or "_treina" in st.session_state.user_logado

# 4. MENU LATERAL
st.sidebar.image("https://www.mideacarrier.com.br/wp-content/themes/midea-carrier/assets/img/logo-midea-carrier.png", width=120)
st.sidebar.write(f"👤 **{st.session_state.user_logado}**")
menu = st.sidebar.radio("Navegação", ["📢 Feed", "🎓 Formação Continuada", "⚙️ Gestão & Reports"])

if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()

# --- TELA: FEED ---
if menu == "📢 Feed":
    st.title("📢 Feed da Operação")
    feed = carregar_dados(FEED_FILE)
    for i, post in enumerate(feed):
        with st.chat_message("user", avatar="❄️"):
            st.write(f"**[{post.get('data')}]** {post.get('msg')}")
            if post.get('img'): st.image(post['img'])
            if st.button(f"❤️ {post.get('curtidas', 0)}", key=f"lk_{i}"):
                feed[i]['curtidas'] = post.get('curtidas', 0) + 1
                salvar_dados(feed, FEED_FILE); st.rerun()

# --- TELA: FORMAÇÃO CONTINUADA ---
elif menu == "🎓 Formação Continuada":
    st.title("🎓 Treinamentos")
    treinos = carregar_dados(TREINAMENTOS_FILE)
    
    if not treinos:
        st.info("Nenhum treinamento disponível.")
    
    for idx, t in enumerate(treinos):
        with st.expander(f"📺 {t['titulo']}"):
            st.video(t['video_url'])
            st.divider()
            st.subheader("📝 Avaliação")
            
            respostas_usuario = {}
            for q_idx, q in enumerate(t['questoes']):
                respostas_usuario[q_idx] = st.radio(f"{q_idx+1}. {q['pergunta']}", q['opcoes'], key=f"q_{idx}_{q_idx}")
            
            if st.button("Finalizar Prova", key=f"btn_p_{idx}"):
                total = len(t['questoes'])
                acertos = sum(1 for q_idx, q in enumerate(t['questoes']) if respostas_usuario[q_idx] == q['correta'])
                nota = (acertos / total) * 10
                
                notas = carregar_dados(NOTAS_FILE)
                notas.append({
                    "usuario": st.session_state.user_logado,
                    "treinamento": t['titulo'],
                    "nota": nota,
                    "data": datetime.now().strftime("%d/%m/%Y %H:%M")
                })
                salvar_dados(notas, NOTAS_FILE)
                
                if nota >= 7: st.success(f"Aprovado! Nota: {nota}")
                else: st.error(f"Reprovado. Nota: {nota}. Estude o material novamente.")

# --- TELA: GESTÃO & REPORTS ---
elif menu == "⚙️ Gestão & Reports":
    if e_gestor:
        t1, t2 = st.tabs(["🆕 Novo Treinamento", "📊 Relatórios de Performance"])
        
        with t1:
            st.subheader("Cadastro de Módulo")
            titulo_t = st.text_input("Nome do Treinamento")
            url_t = st.text_input("Link do Vídeo")
            
            # Sistema de múltiplas perguntas
            if 'temp_questoes' not in st.session_state: st.session_state.temp_questoes = []
            
            with st.container():
                st.write("--- Adicionar Pergunta ---")
                perg = st.text_input("Pergunta/Questão")
                colA, colB, colC = st.columns(3)
                o1 = colA.text_input("Opção 1")
                o2 = colB.text_input("Opção 2")
                o3 = colC.text_input("Opção 3")
                resp = st.selectbox("Qual é a correta?", [o1, o2, o3])
                
                if st.button("➕ Adicionar Pergunta à Prova"):
                    if perg and o1:
                        st.session_state.temp_questoes.append({
                            "pergunta": perg, "opcoes": [o1, o2, o3], "correta": resp
                        })
                        st.toast("Pergunta adicionada!")
            
            st.write(f"📦 Questões preparadas: {len(st.session_state.temp_questoes)}")
            
            if st.button("💾 SALVAR TREINAMENTO COMPLETO"):
                if titulo_t and st.session_state.temp_questoes:
                    todos_treinos = carregar_dados(TREINAMENTOS_FILE)
                    todos_treinos.append({
                        "titulo": titulo_t,
                        "video_url": url_t,
                        "questoes": st.session_state.temp_questoes
                    })
                    salvar_dados(todos_treinos, TREINAMENTOS_FILE)
                    st.session_state.temp_questoes = [] # Limpa a lista temporária
                    st.success("Módulo de treinamento publicado!")
                    st.rerun()

        with t2:
            st.subheader("Relatório de Notas")
            df_notas = pd.DataFrame(carregar_dados(NOTAS_FILE))
            if not df_notas.empty:
                st.dataframe(df_notas, use_container_width=True)
                st.download_button("Exportar CSV", df_notas.to_csv(index=False), "relatorio_notas.csv")
            
            st.divider()
            st.subheader("Engajamento do Feed")
            df_f = pd.DataFrame(carregar_dados(FEED_FILE))
            if not df_f.empty and 'curtidas' in df_f.columns:
                st.bar_chart(df_f.set_index('msg')['curtidas'])
    else:
        st.error("Acesso restrito ao time de Gestão e Treinamento.")
