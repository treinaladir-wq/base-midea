import streamlit as st
import os
import json
import base64
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DE ACESSO RÁPIDO (LOGO) ---
# Se quiser usar imagem no futuro, basta colar o ID do Google Drive entre as aspas.
ID_DRIVE_LOGO = "1ByGFCJI5ZkuakRG5E1DnCExEwBXzykei" 
URL_LOGO = "https://lh3.googleusercontent.com/d/1ByGFCJI5ZkuakRG5E1DnCExEwBXzykei" if ID_DRIVE_LOGO else None

# 1. CONFIGURAÇÃO VISUAL
st.set_page_config(page_title="Midea | Operação & Treinamento", layout="wide", page_icon="❄️")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    .stButton>button { 
        background: linear-gradient(90deg, #005596 0%, #5c2d91 100%); 
        color: white; border: none; font-weight: bold; border-radius: 8px; width: 100%;
    }
    .btn-gestao>div>button { background: #6c757d !important; color: white !important; height: 32px; font-size: 11px; margin-bottom: 5px;}
    .btn-perigo>div>button { background: #d9534f !important; color: white !important; height: 32px; font-size: 11px; }
    .comment-box { background-color: #f8f9fa; padding: 8px; border-radius: 5px; margin-top: 5px; border-left: 3px solid #5c2d91; font-size: 0.9em; }
    h1, h2, h3 { color: #005596; border-bottom: 1px solid #ddd; padding-bottom: 10px; }
    .stExpander { border: 1px solid #e6e6e6; border-radius: 8px !important; margin-bottom: 10px; background-color: white; }
    </style>
    """, unsafe_allow_html=True)

# 2. BANCO DE DADOS LOCAIS
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

# 3. SISTEMA DE LOGIN
if 'autenticado' not in st.session_state: st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if URL_LOGO and ID_DRIVE_LOGO:
            st.image(URL_LOGO, width=600)
        else:
            st.title("❄️ Portal Midea")
            st.subheader("Operação & Treinamento")
        
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("ACESSAR PORTAL"):
            users = st.secrets.get("passwords", {"admin": "midea123"})
            if u in users and str(users[u]) == p:
                st.session_state.autenticado, st.session_state.user_logado = True, u
                st.rerun()
            else: st.error("Usuário ou senha inválidos.")
    st.stop()

# Define se é Gestor (TL / Treinamento)
e_gestor = "_admin" in st.session_state.user_logado or "_treina" in st.session_state.user_logado

# 4. MENU LATERAL
if URL_LOGO and ID_DRIVE_LOGO:
    st.sidebar.image(URL_LOGO, width=300)
else:
    st.sidebar.title("❄️ Midea")

nome_exibicao = st.session_state.user_logado.split('_')[0].capitalize()

st.sidebar.markdown(f"👤 **Bem-vindo, {nome_exibicao}**")
menu = st.sidebar.radio("Navegação", ["📢 Feed da Operação", "🎓 Formação Continuada", "⚙️ Gestão & Reports"])

if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()

# --- TELA: FEED DA OPERAÇÃO ---
if menu == "📢 Feed da Operação":
    st.title("📢 Comunicados e Avisos")
    feed = carregar_dados(FEED_FILE)
    
    for i, post in enumerate(feed):
        with st.chat_message("user", avatar="❄️"):
            col_txt, col_ctrl = st.columns([0.8, 0.2])
            
            with col_txt:
                st.write(f"📅 **{post.get('data')}**")
                edit_key = f"edit_mode_{i}"
                if e_gestor and st.session_state.get(edit_key):
                    nova_msg = st.text_area("Editar postagem:", post.get('msg'), key=f"area_{i}")
                    if st.button("Salvar Alteração", key=f"save_{i}"):
                        feed[i]['msg'] = nova_msg
                        salvar_dados(feed, FEED_FILE); st.session_state[edit_key] = False; st.rerun()
                else:
                    st.write(post.get('msg'))

            if e_gestor:
                with col_ctrl:
                    st.markdown('<div class="btn-gestao">', unsafe_allow_html=True)
                    if st.button("✏️ Editar", key=f"btn_ed_{i}"): st.session_state[edit_key] = True; st.rerun()
                    if st.button("🗑️ Excluir", key=f"btn_del_{i}"): feed.pop(i); salvar_dados(feed, FEED_FILE); st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

            if post.get('img'): st.image(post['img'])
            
            # Interação de Curtidas (Log por Usuário)
            likes = post.get('curtidas_usuarios', [])
            if st.button(f"❤️ {len(likes)} Curtidas", key=f"lk_{i}"):
                if st.session_state.user_logado not in likes:
                    likes.append(st.session_state.user_logado)
                    feed[i]['curtidas_usuarios'] = likes
                    salvar_dados(feed, FEED_FILE); st.rerun()
            
            # Comentários
            coments = post.get('comentarios', [])
            with st.expander(f"💬 Comentários ({len(coments)})"):
                for c in coments:
                    st.markdown(f'<div class="comment-box"><b>{c["user"]}:</b> {c["txt"]} <br><small>{c.get("data", "")}</small></div>', unsafe_allow_html=True)
                nc = st.text_input("Escreva um comentário...", key=f"in_{i}")
                if st.button("Publicar", key=f"bt_{i}"):
                    if nc:
                        if 'comentarios' not in feed[i]: feed[i]['comentarios'] = []
                        feed[i]['comentarios'].append({
                            "user": st.session_state.user_logado, 
                            "txt": nc, 
                            "data": datetime.now().strftime("%d/%m/%Y %H:%M")
                        })
                        salvar_dados(feed, FEED_FILE); st.rerun()

# --- TELA: FORMAÇÃO CONTINUADA ---
elif menu == "🎓 Formação Continuada":
    st.title("🎓 Centro de Treinamento")
    treinos = carregar_dados(TREINAMENTOS_FILE)
    if not treinos: st.info("Nenhum treinamento disponível.")
    
    for idx, t in enumerate(treinos):
        with st.expander(f"📺 MÓDULO: {t['titulo']}"):
            st.video(t['video_path'])
            st.divider()
            st.subheader("📝 Avaliação de Conhecimento")
            respostas_agente = {}
            for q_idx, q in enumerate(t['questoes']):
                respostas_agente[q_idx] = st.radio(f"{q_idx+1}. {q['pergunta']}", q['opcoes'], key=f"q_{idx}_{q_idx}")
            
            if st.button("Finalizar e Enviar", key=f"btn_p_{idx}"):
                acertos = sum(1 for q_idx, q in enumerate(t['questoes']) if respostas_agente[q_idx] == q['correta'])
                nota = (acertos / len(t['questoes'])) * 10
                notas = carregar_dados(NOTAS_FILE)
                notas.append({
                    "usuario": st.session_state.user_logado, 
                    "treinamento": t['titulo'], 
                    "nota": nota, 
                    "data": datetime.now().strftime("%d/%m/%Y %H:%M")
                })
                salvar_dados(notas, NOTAS_FILE)
                if nota >= 7: st.success(f"Parabéns! Você foi aprovado com nota {nota}")
                else: st.warning(f"Sua nota foi {nota}. Sugerimos revisar o vídeo.")

# --- TELA: GESTÃO & REPORTS ---
elif menu == "⚙️ Gestão & Reports":
    if e_gestor:
        t_feed, t_treino, t_audit = st.tabs(["📢 Novo Post", "🎓 Novo Treinamento", "📊 Auditoria & Logs"])
        
        with t_feed:
            msg_f = st.text_area("Texto do comunicado")
            img_f = st.file_uploader("Anexar Imagem", type=['png', 'jpg', 'jpeg'])
            if st.button("Enviar para o Feed"):
                img_b64 = f"data:image/png;base64,{base64.b64encode(img_f.read()).decode()}" if img_f else None
                f = carregar_dados(FEED_FILE)
                f.insert(0, {
                    "id": datetime.now().strftime("%Y%m%d%H%M%S"), 
                    "data": datetime.now().strftime("%d/%m/%Y %H:%M"), 
                    "msg": msg_f, 
                    "img": img_b64, 
                    "curtidas_usuarios": [], 
                    "comentarios": []
                })
                salvar_dados(f, FEED_FILE); st.success("Comunicado publicado com sucesso!"); st.rerun()

        with t_treino:
            st.subheader("Configurar Novo Módulo")
            tit_a = st.text_input("Nome do Treinamento")
            vid_a = st.file_uploader("Arquivo de Vídeo (MP4)", type=['mp4'])
            if 'temp_q' not in st.session_state: st.session_state.temp_q = []
            
            with st.container():
                st.write("---")
                p_t = st.text_input("Pergunta")
                c1, c2, c3 = st.columns(3)
                oA, oB, oC = c1.text_input("Opção A"), c2.text_input("Opção B"), c3.text_input("Opção C")
                corr = st.selectbox("Alternativa Correta", [oA, oB, oC])
                if st.button("➕ Adicionar Pergunta"):
                    st.session_state.temp_q.append({"pergunta": p_t, "opcoes": [oA, oB, oC], "correta": corr}); st.rerun()

            if st.button("💾 SALVAR TREINAMENTO COMPLETO"):
                if tit_a and vid_a and st.session_state.temp_q:
                    path = os.path.join(VIDEO_DIR, vid_a.name)
                    with open(path, "wb") as f: f.write(vid_a.getbuffer())
                    dt = carregar_dados(TREINAMENTOS_FILE)
                    dt.append({"titulo": tit_a, "video_path": path, "questoes": st.session_state.temp_q})
                    salvar_dados(dt, TREINAMENTOS_FILE); st.session_state.temp_q = []; st.success("Treinamento Salvo!"); st.rerun()

        with t_audit:
            st.subheader("📊 Relatório de Interações (Feed)")
            f_data = carregar_dados(FEED_FILE)
            logs = []
            for post in f_data:
                res = post.get('msg', '')[:40] + "..."
                for u_lk in post.get('curtidas_usuarios', []):
                    logs.append({"Data": post.get('data'), "Post": res, "Usuário": u_lk, "Ação": "Curtiu ❤️"})
                for com in post.get('comentarios', []):
                    logs.append({"Data": com.get('data'), "Post": res, "Usuário": com.get('user'), "Ação": f"Comentou: {com.get('txt')}"})
            
            if logs:
                df_l = pd.DataFrame(logs)
                st.dataframe(df_l, use_container_width=True)
                st.download_button("📥 Exportar Logs de Interação", df_l.to_csv(index=False).encode('utf-8-sig'), "logs_feed.csv")
            else: st.info("Sem interações registradas.")

            st.divider()
            st.subheader("📝 Notas dos Agentes")
            df_n = pd.DataFrame(carregar_dados(NOTAS_FILE))
            if not df_n.empty:
                st.dataframe(df_n, use_container_width=True)
                st.download_button("📥 Exportar Notas (CSV)", df_n.to_csv(index=False).encode('utf-8-sig'), "notas_agentes.csv")
    else: st.error("Acesso restrito.")
