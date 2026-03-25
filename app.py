import streamlit as st
import os
import json
import base64
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO VISUAL (Padrão Midea/Concentrix)
st.set_page_config(page_title="Midea | Formação Continuada", layout="wide", page_icon="🎓")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    .stButton>button { 
        background: linear-gradient(90deg, #005596 0%, #5c2d91 100%); 
        color: white; border: none; font-weight: bold; border-radius: 8px; width: 100%;
    }
    .btn-gestao>div>button { background: #6c757d !important; color: white !important; height: 32px; font-size: 12px; margin-bottom: 5px;}
    .btn-perigo>div>button { background: #d9534f !important; color: white !important; height: 32px; font-size: 12px; }
    .comment-box { background-color: #f8f9fa; padding: 8px; border-radius: 5px; margin-top: 5px; border-left: 3px solid #5c2d91; font-size: 0.9em; }
    h1, h2, h3 { color: #005596; }
    .stExpander { border: 1px solid #e6e6e6; border-radius: 8px !important; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. PERSISTÊNCIA E DIRETÓRIOS
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

# 3. LOGIN E PERMISSÕES
if 'autenticado' not in st.session_state: st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.image("https://www.mideacarrier.com.br/wp-content/themes/midea-carrier/assets/img/logo-midea-carrier.png", width=250)
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("ACESSAR SISTEMA"):
            users = st.secrets.get("passwords", {"admin": "midea123"})
            if u in users and str(users[u]) == p:
                st.session_state.autenticado, st.session_state.user_logado = True, u
                st.rerun()
            else: st.error("Usuário ou senha incorretos.")
    st.stop()

# Identifica se é Gestor (Admin ou Treinamento) pelo sufixo no nome
e_gestor = "_admin" in st.session_state.user_logado or "_treina" in st.session_state.user_logado

# 4. MENU LATERAL
st.sidebar.image("https://www.mideacarrier.com.br/wp-content/themes/midea-carrier/assets/img/logo-midea-carrier.png", width=120)
st.sidebar.write(f"👤 **{st.session_state.user_logado}**")
menu = st.sidebar.radio("Navegação", ["📢 Feed da Operação", "🎓 Formação Continuada", "⚙️ Gestão & Reports"])

if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()

# --- TELA: FEED ---
if menu == "📢 Feed da Operação":
    st.title("📢 Comunicados")
    feed = carregar_dados(FEED_FILE)
    
    for i, post in enumerate(feed):
        with st.chat_message("user", avatar="❄️"):
            col_txt, col_ctrl = st.columns([0.8, 0.2])
            
            with col_txt:
                st.write(f"**[{post.get('data')}]**")
                edit_key = f"edit_mode_{i}"
                if e_gestor and st.session_state.get(edit_key):
                    nova_msg = st.text_area("Editar mensagem:", post.get('msg'), key=f"area_{i}")
                    if st.button("Salvar Alteração", key=f"save_{i}"):
                        feed[i]['msg'] = nova_msg
                        salvar_dados(feed, FEED_FILE)
                        st.session_state[edit_key] = False
                        st.rerun()
                else:
                    st.write(post.get('msg'))

            if e_gestor:
                with col_ctrl:
                    st.markdown('<div class="btn-gestao">', unsafe_allow_html=True)
                    if st.button("✏️ Editar", key=f"btn_ed_{i}"):
                        st.session_state[edit_key] = True
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('<div class="btn-perigo">', unsafe_allow_html=True)
                    if st.button("🗑️ Excluir", key=f"btn_del_{i}"):
                        feed.pop(i); salvar_dados(feed, FEED_FILE); st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

            if post.get('img'): st.image(post['img'])
            
            # Interações
            c_lk, _ = st.columns([0.15, 0.85])
            if c_lk.button(f"❤️ {post.get('curtidas', 0)}", key=f"lk_{i}"):
                feed[i]['curtidas'] = post.get('curtidas', 0) + 1
                salvar_dados(feed, FEED_FILE); st.rerun()

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
    st.title("🎓 Treinamentos Disponíveis")
    treinos = carregar_dados(TREINAMENTOS_FILE)
    
    if not treinos: st.info("Nenhum treinamento publicado.")
    
    for idx, t in enumerate(treinos):
        with st.expander(f"📺 MÓDULO: {t['titulo']}"):
            st.video(t['video_path'])
            st.divider()
            st.subheader("📝 Avaliação de Conhecimento")
            
            respostas = {}
            for q_idx, q in enumerate(t['questoes']):
                respostas[q_idx] = st.radio(f"{q_idx+1}. {q['pergunta']}", q['opcoes'], key=f"q_{idx}_{q_idx}")
            
            if st.button("Finalizar e Enviar", key=f"btn_p_{idx}"):
                acertos = sum(1 for q_idx, q in enumerate(t['questoes']) if respostas[q_idx] == q['correta'])
                nota = (acertos / len(t['questoes'])) * 10
                notas = carregar_dados(NOTAS_FILE)
                notas.append({"usuario": st.session_state.user_logado, "treinamento": t['titulo'], "nota": nota, "data": datetime.now().strftime("%d/%m/%Y %H:%M")})
                salvar_dados(notas, NOTAS_FILE)
                if nota >= 7: st.success(f"Excelente! Nota: {nota}")
                else: st.error(f"Nota: {nota}. Revise o vídeo e tente novamente.")

# --- TELA: GESTÃO & REPORTS ---
elif menu == "⚙️ Gestão & Reports":
    if e_gestor:
        t_feed, t_treino, t_rep = st.tabs(["📢 Novo Post", "🎓 Novo Treinamento", "📊 Relatórios"])
        
        with t_feed:
            msg = st.text_area("O que deseja comunicar?")
            img = st.file_uploader("Anexar Imagem", type=['png', 'jpg', 'jpeg'])
            if st.button("Publicar no Feed"):
                img_b64 = f"data:image/png;base64,{base64.b64encode(img.read()).decode()}" if img else None
                f = carregar_dados(FEED_FILE)
                f.insert(0, {"id": datetime.now().strftime("%Y%m%d%H%M%S"), "data": datetime.now().strftime("%d/%m/%Y %H:%M"), "msg": msg, "img": img_b64, "curtidas": 0, "comentarios": []})
                salvar_dados(f, FEED_FILE); st.success("Postado!"); st.rerun()

        with t_treino:
            tit = st.text_input("Título do Treinamento")
            vid = st.file_uploader("Upload do Vídeo", type=['mp4', 'mov', 'avi'])
            if 'temp_q' not in st.session_state: st.session_state.temp_q = []
            
            st.write("--- Perguntas ---")
            perg = st.text_input("Pergunta")
            o1, o2, o3 = st.text_input("Opção A"), st.text_input("Opção B"), st.text_input("Opção C")
            corr = st.selectbox("Correta", [o1, o2, o3])
            if st.button("➕ Adicionar Pergunta"):
                st.session_state.temp_q.append({"pergunta": perg, "opcoes": [o1, o2, o3], "correta": corr})
                st.toast("Adicionada!"); st.rerun()
            
            st.write(f"Questões na prova: {len(st.session_state.temp_q)}")
            if st.button("💾 SALVAR MÓDULO COMPLETO"):
                if tit and vid and st.session_state.temp_q:
                    v_path = os.path.join(VIDEO_DIR, vid.name)
                    with open(v_path, "wb") as f: f.write(vid.getbuffer())
                    d = carregar_dados(TREINAMENTOS_FILE)
                    d.append({"titulo": tit, "video_path": v_path, "questoes": st.session_state.temp_q})
                    salvar_dados(d, TREINAMENTOS_FILE)
                    st.session_state.temp_q = []; st.success("Publicado!"); st.rerun()

        with t_rep:
            st.subheader("Notas das Provas")
            df = pd.DataFrame(carregar_dados(NOTAS_FILE))
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                st.download_button("Exportar CSV", df.to_csv(index=False), "notas.csv")
    else:
        st.error("Área restrita à Gestão.")
