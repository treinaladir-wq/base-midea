import streamlit as st
import os
import json
import base64
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DE ACESSO RÁPIDO (LOGO) ---
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
    .comment-box { background-color: #f8f9fa; padding: 8px; border-radius: 5px; margin-top: 5px; border-left: 3px solid #5c2d91; font-size: 0.9em; }
    h1, h2, h3 { color: #005596; border-bottom: 1px solid #ddd; padding-bottom: 10px; }
    .stExpander { border: 1px solid #e6e6e6; border-radius: 8px !important; margin-bottom: 10px; background-color: white; }
    </style>
    """, unsafe_allow_html=True)

# 2. BANCO DE DADOS LOCAIS E FUNÇÕES
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

# 3. SISTEMA DE LOGIN (SECRETS COM TIME)
if 'autenticado' not in st.session_state: st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if URL_LOGO: st.image(URL_LOGO, width=400)
        else: st.title("❄️ Portal Midea")
        
        u = st.text_input("Usuário (nome_matricula)")
        p = st.text_input("Senha", type="password")
        if st.button("ACESSAR PORTAL"):
            user_info = st.secrets.get("passwords", {}).get(u)
            if user_info and ";" in user_info:
                senha_correta, time_cadastrado = user_info.split(";")
                if p == senha_correta:
                    st.session_state.autenticado = True
                    st.session_state.user_logado = u
                    st.session_state.user_time = time_cadastrado
                    st.rerun()
                else: st.error("Senha incorreta.")
            else: st.error("Usuário não encontrado ou formato inválido.")
    st.stop()

# --- NOVA LÓGICA DE PERFIS ---
user_id = st.session_state.user_logado.lower()
e_admin = "_admin" in user_id
e_treina = "_treina" in user_id or e_admin
e_tl = "_tl" in user_id or e_admin
# Gestor é qualquer um que possa ver a aba de Gestão
e_gestor = e_admin or e_treina or e_tl 

nome_exibicao = st.session_state.user_logado.split('_')[0].capitalize()
meu_time = st.session_state.get('user_time', 'Geral')

# 4. MENU LATERAL
if URL_LOGO: st.sidebar.image(URL_LOGO, width=250)
st.sidebar.markdown(f"👤 **Bem-vindo, {nome_exibicao}**")
st.sidebar.caption(f"Setor: {meu_time}")

# Menu dinâmico: Gestão só aparece para perfis autorizados
opcoes = ["📢 Feed da Operação", "🎓 Formação Continuada"]
if e_gestor: opcoes.append("⚙️ Gestão & Reports")
menu = st.sidebar.radio("Navegação", opcoes)

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
                if e_gestor and st.session_state.get(edit_key): # Apenas gestores editam
                    nova_msg = st.text_area("Editar postagem:", post.get('msg'), key=f"area_{i}")
                    if st.button("Salvar Alteração", key=f"save_{i}"):
                        feed[i]['msg'] = nova_msg
                        salvar_dados(feed, FEED_FILE); st.session_state[edit_key] = False; st.rerun()
                else: st.write(post.get('msg'))

            if e_gestor: # Apenas gestores vêem botões de edição/exclusão
                with col_ctrl:
                    st.markdown('<div class="btn-gestao">', unsafe_allow_html=True)
                    if st.button("✏️", key=f"btn_ed_{i}"): st.session_state[edit_key] = True; st.rerun()
                    if st.button("🗑️", key=f"btn_del_{i}"): feed.pop(i); salvar_dados(feed, FEED_FILE); st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

            if post.get('img'): st.image(post['img'])
            
            likes = post.get('curtidas_usuarios', [])
            if st.button(f"❤️ {len(likes)} Curtidas", key=f"lk_{i}"):
                if st.session_state.user_logado not in likes:
                    likes.append(st.session_state.user_logado)
                    feed[i]['curtidas_usuarios'] = likes
                    salvar_dados(feed, FEED_FILE); st.rerun()
            
            coments = post.get('comentarios', [])
            with st.expander(f"💬 Comentários ({len(coments)})"):
                for c in coments:
                    nome_coment = c["user"].split("_")[0].capitalize()
                    st.markdown(f'<div class="comment-box"><b>{nome_coment}:</b> {c["txt"]}</div>', unsafe_allow_html=True)
                nc = st.text_input("Escreva um comentário...", key=f"in_{i}")
                if st.button("Publicar", key=f"bt_{i}"):
                    if nc:
                        if 'comentarios' not in feed[i]: feed[i]['comentarios'] = []
                        feed[i]['comentarios'].append({"user": st.session_state.user_logado, "txt": nc, "data": datetime.now().strftime("%d/%m/%Y %H:%M")})
                        salvar_dados(feed, FEED_FILE); st.rerun()

# --- TELA: FORMAÇÃO CONTINUADA ---
elif menu == "🎓 Formação Continuada":
    st.title("🎓 Centro de Treinamento")
    treinos = carregar_dados(TREINAMENTOS_FILE)
    visiveis = [t for t in treinos if "Todos" in t.get('times', []) or meu_time in t.get('times', [])]

    if not visiveis: st.info(f"Nenhum treinamento pendente para o setor {meu_time}.")
    
    for idx, t in enumerate(visiveis):
        with st.expander(f"📺 MÓDULO: {t['titulo']}"):
            st.video(t['video_path'])
            st.divider()
            st.subheader("📝 Avaliação")
            respostas_agente = {}
            for q_idx, q in enumerate(t['questoes']):
                respostas_agente[q_idx] = st.radio(f"{q_idx+1}. {q['pergunta']}", q['opcoes'], key=f"q_{idx}_{q_idx}")
            
            if st.button("Finalizar e Enviar", key=f"btn_p_{idx}"):
                acertos = sum(1 for q_idx, q in enumerate(t['questoes']) if respostas_agente[q_idx] == q['correta'])
                nota = (acertos / len(t['questoes'])) * 10
                notas = carregar_dados(NOTAS_FILE)
                notas.append({"usuario": st.session_state.user_logado, "time": meu_time, "treinamento": t['titulo'], "nota": nota, "data": datetime.now().strftime("%d/%m/%Y %H:%M")})
                salvar_dados(notas, NOTAS_FILE)
                st.success(f"Avaliação enviada! Nota: {nota}")

# --- TELA: GESTÃO & REPORTS ---
elif menu == "⚙️ Gestão & Reports":
    if e_gestor:
        # Define quais abas aparecem para cada perfil
        tabs_list = []
        if e_tl or e_treina: tabs_list.append("📢 Novo Post")
        if e_treina: tabs_list.append("🎓 Novo Treinamento")
        if e_admin or e_tl: tabs_list.append("📊 Auditoria & Logs")
        
        # Cria as abas dinamicamente
        active_tabs = st.tabs(tabs_list)
        
        if "📢 Novo Post" in tabs_list:
            with active_tabs[tabs_list.index("📢 Novo Post")]:
                msg_f = st.text_area("Texto do comunicado")
                img_f = st.file_uploader("Imagem", type=['png', 'jpg'])
                if st.button("Publicar no Feed"):
                    img_b64 = f"data:image/png;base64,{base64.b64encode(img_f.read()).decode()}" if img_f else None
                    f = carregar_dados(FEED_FILE)
                    f.insert(0, {"id": datetime.now().strftime("%Y%m%d%H%M%S"), "data": datetime.now().strftime("%d/%m/%Y %H:%M"), "msg": msg_f, "img": img_b64, "curtidas_usuarios": [], "comentarios": []})
                    salvar_dados(f, FEED_FILE); st.success("Publicado!"); st.rerun()

        if "🎓 Novo Treinamento" in tabs_list:
            with active_tabs[tabs_list.index("🎓 Novo Treinamento")]:
                st.subheader("Novo Treinamento")
                tit_a = st.text_input("Título do Módulo")
                times_alvo = st.multiselect("Destinar para os times:", ["Todos", "0800 Voz", "0800 Chat", "RECLAME AQUI", "MIDIAS SOCIAIS", "SAC REVENDA", "E-TICKET", "BACKOFFICE", "BACKOFFICE RECALL", "LAD", "RAC & REF", "SUPORTE TÉCNICO", "MIDEA CLUB", "JIRA"], default=["Todos"])
                vid_a = st.file_uploader("Vídeo (MP4)", type=['mp4'])
                
                if 'temp_q' not in st.session_state: st.session_state.temp_q = []
                with st.form("pergunta_form"):
                    p_t = st.text_input("Pergunta")
                    c1, c2, c3 = st.columns(3)
                    oA, oB, oC = c1.text_input("Opção A"), c2.text_input("Opção B"), c3.text_input("Opção C")
                    corr = st.selectbox("Correta", [oA, oB, oC])
                    if st.form_submit_button("Adicionar Pergunta"):
                        st.session_state.temp_q.append({"pergunta": p_t, "opcoes": [oA, oB, oC], "correta": corr})
                
                if st.button("💾 SALVAR TUDO"):
                    if tit_a and vid_a:
                        path = os.path.join(VIDEO_DIR, vid_a.name)
                        with open(path, "wb") as f: f.write(vid_a.getbuffer())
                        dt = carregar_dados(TREINAMENTOS_FILE)
                        dt.append({"titulo": tit_a, "video_path": path, "questoes": st.session_state.temp_q, "times": times_alvo})
                        salvar_dados(dt, TREINAMENTOS_FILE); st.session_state.temp_q = []; st.success("Salvo!"); st.rerun()

        if "📊 Auditoria & Logs" in tabs_list:
            with active_tabs[tabs_list.index("📊 Auditoria & Logs")]:
                st.subheader("📊 Relatórios em CSV")
                
                # Relatório de Notas (Filtro por time para TL)
                df_n = pd.DataFrame(carregar_dados(NOTAS_FILE))
                if not df_n.empty:
                    if not e_admin: # Se for TL, vê apenas o seu time
                        df_n = df_n[df_n['time'] == meu_time]
                    
                    st.dataframe(df_n, use_container_width=True)
                    csv_notas = df_n.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("📥 Baixar Notas (.csv)", csv_notas, "notas_agentes.csv", "text/csv")
                else:
                    st.info("Nenhuma nota registrada ainda.")
    else: 
        st.error("Acesso restrito.")
