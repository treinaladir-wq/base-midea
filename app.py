import streamlit as st
import os
import json
import base64
import pandas as pd
from datetime import datetime
from io import BytesIO

# --- CONFIGURAÇÃO DE ACESSO RÁPIDO (LOGO) ---
ID_DRIVE_LOGO = "1ByGFCJI5ZkuakRG5E1DnCExEwBXzykei" 
URL_LOGO = "https://lh3.googleusercontent.com/d/1ByGFCJI5ZkuakRG5E1DnCExEwBXzykei" if ID_DRIVE_LOGO else None

# 1. CONFIGURAÇÃO VISUAL E DE PÁGINA
st.set_page_config(page_title="Midea | Operação & Treinamento", layout="wide", page_icon="❄️")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    .stButton>button { 
        background: linear-gradient(90deg, #005596 0%, #5c2d91 100%); 
        color: white; border: none; font-weight: bold; border-radius: 8px; width: 100%;
    }
    .btn-gestao>div>button { background: #6c757d !important; color: white !important; height: 32px; font-size: 11px; margin-bottom: 5px;}
    .comment-box { background-color: #f8f9fa; padding: 8px; border-radius: 5px; margin-top: 5px; border-left: 3px solid #5c2d91; font-size: 0.9em; }
    h1, h2, h3 { color: #005596; border-bottom: 1px solid #ddd; padding-bottom: 10px; }
    .stExpander { border: 1px solid #e6e6e6; border-radius: 8px !important; margin-bottom: 10px; background-color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES AUXILIARES ---
def carregar_dados(arquivo):
    if os.path.exists(arquivo):
        with open(arquivo, "r") as f: return json.load(f)
    return []

def salvar_dados(dados, arquivo):
    with open(arquivo, "w") as f: json.dump(dados, f)

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Relatorio')
    return output.getvalue()

# 2. BANCO DE DADOS LOCAIS
FEED_FILE = "feed_data.json"
TREINAMENTOS_FILE = "treinamentos.json"
NOTAS_FILE = "notas_provas.json"
VIDEO_DIR = "videos"
if not os.path.exists(VIDEO_DIR): os.makedirs(VIDEO_DIR)

# 3. SISTEMA DE LOGIN
if 'autenticado' not in st.session_state: st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if URL_LOGO: st.image(URL_LOGO, width=600)
        else: st.title("❄️ Portal Midea")
        
        u = st.text_input("Usuário (nome_matricula)")
        p = st.text_input("Senha", type="password")
        if st.button("ACESSAR PORTAL"):
            # Exemplo de credenciais em secrets ou padrão
            users = st.secrets.get("passwords", {"admin_00000": "midea123"})
            if u in users and str(users[u]) == p:
                st.session_state.autenticado, st.session_state.user_logado = True, u
                st.rerun()
            else: st.error("Usuário ou senha inválidos.")
    st.stop()

# Lógica de Nome e Perfil
e_gestor = "_admin" in st.session_state.user_logado or "_treina" in st.session_state.user_logado
nome_exibicao = st.session_state.user_logado.split('_')[0].capitalize()

# 4. MENU LATERAL
if URL_LOGO: st.sidebar.image(URL_LOGO, width=300)
st.sidebar.markdown(f"👤 **Bem-vindo, {nome_exibicao}**")
menu = st.sidebar.radio("Navegação", ["📢 Feed da Operação", "🎓 Formação Continuada", "⚙️ Gestão & Reports"])

if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()

# --- TELA: FEED DA OPERAÇÃO ---
if menu == "📢 Feed da Operação":
    st.title("📢 Comunicados")
    feed = carregar_dados(FEED_FILE)
    for i, post in enumerate(feed):
        with st.chat_message("user", avatar="❄️"):
            col_txt, col_ctrl = st.columns([0.8, 0.2])
            with col_txt:
                st.write(f"📅 **{post.get('data')}**")
                edit_key = f"edit_mode_{i}"
                if e_gestor and st.session_state.get(edit_key):
                    nova_msg = st.text_area("Editar:", post.get('msg'), key=f"area_{i}")
                    if st.button("Salvar", key=f"save_{i}"):
                        feed[i]['msg'] = nova_msg
                        salvar_dados(feed, FEED_FILE); st.session_state[edit_key] = False; st.rerun()
                else: st.write(post.get('msg'))
            
            if e_gestor:
                with col_ctrl:
                    st.markdown('<div class="btn-gestao">', unsafe_allow_html=True)
                    if st.button("✏️ Editar", key=f"btn_ed_{i}"): st.session_state[edit_key] = True; st.rerun()
                    if st.button("🗑️ Excluir", key=f"btn_del_{i}"): feed.pop(i); salvar_dados(feed, FEED_FILE); st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
            
            if post.get('img'): st.image(post['img'])
            
            # Curtidas e Comentários
            likes = post.get('curtidas_usuarios', [])
            if st.button(f"❤️ {len(likes)}", key=f"lk_{i}"):
                if st.session_state.user_logado not in likes:
                    likes.append(st.session_state.user_logado)
                    feed[i]['curtidas_usuarios'] = likes
                    salvar_dados(feed, FEED_FILE); st.rerun()
            
            coments = post.get('comentarios', [])
            with st.expander(f"💬 Comentários ({len(coments)})"):
                for c in coments:
                    st.markdown(f'<div class="comment-box"><b>{c["user"].split("_")[0].capitalize()}:</b> {c["txt"]}</div>', unsafe_allow_html=True)
                nc = st.text_input("Comentar...", key=f"in_{i}")
                if st.button("Enviar", key=f"bt_{i}"):
                    if nc:
                        if 'comentarios' not in feed[i]: feed[i]['comentarios'] = []
                        feed[i]['comentarios'].append({"user": st.session_state.user_logado, "txt": nc, "data": datetime.now().strftime("%d/%m/%Y %H:%M")})
                        salvar_dados(feed, FEED_FILE); st.rerun()

# --- TELA: FORMAÇÃO CONTINUADA ---
elif menu == "🎓 Formação Continuada":
    st.title("🎓 Treinamentos")
    treinos = carregar_dados(TREINAMENTOS_FILE)
    for idx, t in enumerate(treinos):
        with st.expander(f"📺 {t['titulo']}"):
            st.video(t['video_path'])
            st.divider()
            resp = {}
            for q_idx, q in enumerate(t['questoes']):
                resp[q_idx] = st.radio(f"{q_idx+1}. {q['pergunta']}", q['opcoes'], key=f"q_{idx}_{q_idx}")
            if st.button("Enviar Prova", key=f"btn_p_{idx}"):
                acertos = sum(1 for q_idx, q in enumerate(t['questoes']) if resp[q_idx] == q['correta'])
                nota = (acertos / len(t['questoes'])) * 10
                notas = carregar_dados(NOTAS_FILE)
                notas.append({"usuario": st.session_state.user_logado, "treinamento": t['titulo'], "nota": nota, "data": datetime.now().strftime("%d/%m/%Y %H:%M")})
                salvar_dados(notas, NOTAS_FILE); st.success(f"Nota: {nota}")

# --- TELA: GESTÃO & REPORTS ---
elif menu == "⚙️ Gestão & Reports":
    if e_gestor:
        t1, t2, t3 = st.tabs(["📢 Novo Post", "🎓 Novo Treinamento", "📊 Reports (Excel)"])
        
        with t1:
            msg = st.text_area("Comunicado")
            img = st.file_uploader("Imagem", type=['png', 'jpg'])
            if st.button("Publicar"):
                img_b64 = f"data:image/png;base64,{base64.b64encode(img.read()).decode()}" if img else None
                f = carregar_dados(FEED_FILE)
                f.insert(0, {"id": datetime.now().strftime("%Y%m%d%H%M%S"), "data": datetime.now().strftime("%d/%m/%Y %H:%M"), "msg": msg, "img": img_b64, "curtidas_usuarios": [], "comentarios": []})
                salvar_dados(f, FEED_FILE); st.success("Postado!"); st.rerun()

        with t2:
            tit = st.text_input("Título"); vid = st.file_uploader("Vídeo", type=['mp4'])
            if 'temp_q' not in st.session_state: st.session_state.temp_q = []
            p = st.text_input("Pergunta"); oA, oB, oC = st.text_input("A"), st.text_input("B"), st.text_input("C")
            corr = st.selectbox("Correta", [oA, oB, oC])
            if st.button("➕ Add Pergunta"): st.session_state.temp_q.append({"pergunta": p, "opcoes": [oA, oB, oC], "correta": corr}); st.rerun()
            if st.button("💾 Salvar Módulo"):
                if tit and vid:
                    path = os.path.join(VIDEO_DIR, vid.name)
                    with open(path, "wb") as f: f.write(vid.getbuffer())
                    dt = carregar_dados(TREINAMENTOS_FILE); dt.append({"titulo": tit, "video_path": path, "questoes": st.session_state.temp_q})
                    salvar_dados(dt, TREINAMENTOS_FILE); st.session_state.temp_q = []; st.success("Salvo!"); st.rerun()

        with t3:
            st.subheader("📊 Auditoria de Engajamento")
            f_data = carregar_dados(FEED_FILE)
            logs = []
            for post in f_data:
                res = post.get('msg', '')[:40] + "..."
                for u_lk in post.get('curtidas_usuarios', []):
                    logs.append({"Data": post.get('data'), "Post": res, "Usuário": u_lk, "Matrícula": u_lk.split('_')[-1], "Ação": "Curtiu ❤️"})
                for com in post.get('comentarios', []):
                    logs.append({"Data": com.get('data'), "Post": res, "Usuário": com.get('user'), "Matrícula": com.get('user').split('_')[-1], "Ação": f"Comentou: {com.get('txt')}"})
            
            if logs:
                df_l = pd.DataFrame(logs)
                st.dataframe(df_l, use_container_width=True)
                st.download_button("📥 Baixar Logs (Excel)", to_excel(df_l), "logs_feed.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
            st.divider()
            st.subheader("📝 Notas das Provas")
            df_n = pd.DataFrame(carregar_dados(NOTAS_FILE))
            if not df_n.empty:
                df_n['Matrícula'] = df_n['usuario'].apply(lambda x: x.split('_')[-1])
                st.dataframe(df_n, use_container_width=True)
                st.download_button("📥 Baixar Notas (Excel)", to_excel(df_n), "notas_agentes.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else: st.error("Acesso restrito.")
