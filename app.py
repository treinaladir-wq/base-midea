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
    .comment-box { background-color: #f8f9fa; padding: 8px; border-radius: 5px; margin-top: 5px; border-left: 3px solid #5c2d91; font-size: 0.9em; }
    h1, h2, h3 { color: #005596; }
    </style>
    """, unsafe_allow_html=True)

# 2. PERSISTÊNCIA E PASTAS
FEED_FILE = "feed_data.json"
TREINAMENTOS_FILE = "treinamentos.json"
NOTAS_FILE = "notas_provas.json"
VIDEO_DIR = "videos"

if not os.path.exists(VIDEO_DIR): os.makedirs(VIDEO_DIR)

def carregar_dados(arquivo):
    if os.path.exists(arquivo):
        with open(arquivo, "r") as f: return json.load(f)
    return []

def salvar_dados(dados, arquivo):
    with open(arquivo, "w") as f: json.dump(dados, f)

# 3. LOGIN
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

e_gestor = "_admin" in st.session_state.user_logado or "_treina" in st.session_state.user_logado

# 4. MENU
st.sidebar.image("https://www.mideacarrier.com.br/wp-content/themes/midea-carrier/assets/img/logo-midea-carrier.png", width=120)
menu = st.sidebar.radio("Navegação", ["📢 Feed", "🎓 Formação Continuada", "⚙️ Gestão & Reports"])

# --- TELA: FEED (COM COMENTÁRIOS RESTAURADOS) ---
if menu == "📢 Feed":
    st.title("📢 Feed da Operação")
    feed = carregar_dados(FEED_FILE)
    for i, post in enumerate(feed):
        with st.chat_message("user", avatar="❄️"):
            st.write(f"**[{post.get('data', 'Data n/a')}]** {post.get('msg', '')}")
            if post.get('img'): st.image(post['img'])
            
            # Curtidas
            c_lk, _ = st.columns([0.15, 0.85])
            if c_lk.button(f"❤️ {post.get('curtidas', 0)}", key=f"lk_{i}"):
                feed[i]['curtidas'] = post.get('curtidas', 0) + 1
                salvar_dados(feed, FEED_FILE); st.rerun()
            
            # Comentários
            coments = post.get('comentarios', [])
            with st.expander(f"💬 Comentários ({len(coments)})"):
                for c in coments:
                    st.markdown(f'<div class="comment-box"><b>{c["user"]}:</b> {c["txt"]}</div>', unsafe_allow_html=True)
                
                nc = st.text_input("Escreva um comentário...", key=f"in_{i}")
                if st.button("Enviar", key=f"bt_{i}"):
                    if nc:
                        if 'comentarios' not in feed[i]: feed[i]['comentarios'] = []
                        feed[i]['comentarios'].append({"user": st.session_state.user_logado, "txt": nc})
                        salvar_dados(feed, FEED_FILE); st.rerun()

# --- TELA: FORMAÇÃO CONTINUADA ---
elif menu == "🎓 Formação Continuada":
    st.title("🎓 Treinamentos")
    treinos = carregar_dados(TREINAMENTOS_FILE)
    for idx, t in enumerate(treinos):
        with st.expander(f"📺 {t['titulo']}"):
            # Carrega o arquivo de vídeo local
            st.video(t['video_path'])
            st.divider()
            
            respostas = {}
            for q_idx, q in enumerate(t['questoes']):
                respostas[q_idx] = st.radio(f"{q_idx+1}. {q['pergunta']}", q['opcoes'], key=f"q_{idx}_{q_idx}")
            
            if st.button("Finalizar Prova", key=f"btn_p_{idx}"):
                acertos = sum(1 for q_idx, q in enumerate(t['questoes']) if respostas[q_idx] == q['correta'])
                nota = (acertos / len(t['questoes'])) * 10
                notas = carregar_dados(NOTAS_FILE)
                notas.append({"usuario": st.session_state.user_logado, "treinamento": t['titulo'], "nota": nota, "data": datetime.now().strftime("%d/%m/%Y %H:%M")})
                salvar_dados(notas, NOTAS_FILE)
                st.success(f"Prova enviada! Nota: {nota}")

# --- TELA: GESTÃO & REPORTS ---
elif menu == "⚙️ Gestão & Reports":
    if e_gestor:
        t1, t2 = st.tabs(["🆕 Novo Treinamento", "📊 Relatórios"])
        with t1:
            st.subheader("Cadastro de Módulo")
            titulo_t = st.text_input("Nome do Treinamento")
            # NOVO: Upload de arquivo de vídeo
            video_file = st.file_uploader("Upload do Vídeo (MP4, MOV)", type=['mp4', 'mov', 'avi'])
            
            if 'temp_questoes' not in st.session_state: st.session_state.temp_questoes = []
            
            with st.container():
                st.write("--- Adicionar Perguntas ---")
                perg = st.text_input("Pergunta")
                o1, o2, o3 = st.text_input("A"), st.text_input("B"), st.text_input("C")
                resp = st.selectbox("Correta", [o1, o2, o3])
                if st.button("➕ Adicionar Pergunta"):
                    st.session_state.temp_questoes.append({"pergunta": perg, "opcoes": [o1, o2, o3], "correta": resp})
                    st.toast("Adicionada!")

            if st.button("💾 PUBLICAR TREINAMENTO"):
                if titulo_t and video_file and st.session_state.temp_questoes:
                    # Salva o arquivo fisicamente
                    v_path = os.path.join(VIDEO_DIR, video_file.name)
                    with open(v_path, "wb") as f: f.write(video_file.getbuffer())
                    
                    dados = carregar_dados(TREINAMENTOS_FILE)
                    dados.append({"titulo": titulo_t, "video_path": v_path, "questoes": st.session_state.temp_questoes})
                    salvar_dados(dados, TREINAMENTOS_FILE)
                    st.session_state.temp_questoes = []
                    st.success("Publicado com sucesso!")
                    st.rerun()
        
        with t2:
            st.subheader("Relatório de Notas")
            df = pd.DataFrame(carregar_dados(NOTAS_FILE))
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                st.download_button("Exportar CSV", df.to_csv(index=False), "notas.csv")
    else:
        st.error("Acesso restrito.")
