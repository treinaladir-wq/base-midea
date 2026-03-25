import streamlit as st
import os
import json
import base64
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO VISUAL
st.set_page_config(page_title="Midea | Formação & Operação", layout="wide", page_icon="❄️")

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

# 2. BANCO DE DADOS E PASTAS
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
        st.image("https://lh3.googleusercontent.com/d/1ByGFCJI5ZkuakRG5E1DnCExEwBXzykei")
        p = st.text_input("Senha", type="password")
        if st.button("ACESSAR PORTAL"):
            users = st.secrets.get("passwords", {"admin": "midea123"})
            if u in users and str(users[u]) == p:
                st.session_state.autenticado, st.session_state.user_logado = True, u
                st.rerun()
            else: st.error("Credenciais inválidas.")
    st.stop()

# Permissão por sufixo para TLs e Treinamento
e_gestor = "_admin" in st.session_state.user_logado or "_treina" in st.session_state.user_logado

# 4. NAVEGAÇÃO
st.sidebar.image("https://lh3.googleusercontent.com/d/1ByGFCJI5ZkuakRG5E1DnCExEwBXzykei", width=300)
st.sidebar.markdown(f"👤 **Bem-vindo, {st.session_state.user_logado}, ao Portal Midea**")
menu = st.sidebar.radio("Menu Principal", ["📢 Feed da Operação", "🎓 Formação Continuada", "📊 Gestão & Reports"])

if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()

# --- TELA: FEED ---
if menu == "📢 Feed da Operação":
    st.title("📢 Feed de Comunicados")
    feed = carregar_dados(FEED_FILE)
    
    for i, post in enumerate(feed):
        with st.chat_message("user", avatar="❄️"):
            col_txt, col_ctrl = st.columns([0.8, 0.2])
            
            with col_txt:
                st.write(f"📅 **{post.get('data')}**")
                edit_key = f"edit_mode_{i}"
                if e_gestor and st.session_state.get(edit_key):
                    nova_msg = st.text_area("Editar postagem:", post.get('msg'), key=f"area_{i}")
                    if st.button("Atualizar", key=f"save_{i}"):
                        feed[i]['msg'] = nova_msg
                        salvar_dados(feed, FEED_FILE); st.session_state[edit_key] = False; st.rerun()
                else:
                    st.write(post.get('msg'))

            if e_gestor:
                with col_ctrl:
                    st.markdown('<div class="btn-gestao">', unsafe_allow_html=True)
                    if st.button("✏️ Editar", key=f"btn_ed_{i}"): st.session_state[edit_key] = True; st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('<div class="btn-perigo">', unsafe_allow_html=True)
                    if st.button("🗑️ Excluir", key=f"btn_del_{i}"): feed.pop(i); salvar_dados(feed, FEED_FILE); st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

            if post.get('img'): st.image(post['img'])
            
            # Curtidas com log de usuário
            likes = post.get('curtidas_usuarios', [])
            c_lk, _ = st.columns([0.15, 0.85])
            if c_lk.button(f"❤️ {len(likes)}", key=f"lk_{i}"):
                if st.session_state.user_logado not in likes:
                    likes.append(st.session_state.user_logado)
                    feed[i]['curtidas_usuarios'] = likes
                    salvar_dados(feed, FEED_FILE); st.rerun()
            
            # Comentários
            coments = post.get('comentarios', [])
            with st.expander(f"💬 Comentários ({len(coments)})"):
                for c in coments:
                    st.markdown(f'<div class="comment-box"><b>{c["user"]}:</b> {c["txt"]}</div>', unsafe_allow_html=True)
                nc = st.text_input("Escreva um comentário...", key=f"in_{i}")
                if st.button("Publicar Comentário", key=f"bt_{i}"):
                    if nc:
                        if 'comentarios' not in feed[i]: feed[i]['comentarios'] = []
                        feed[i]['comentarios'].append({"user": st.session_state.user_logado, "txt": nc, "data": datetime.now().strftime("%d/%m/%Y %H:%M")})
                        salvar_dados(feed, FEED_FILE); st.rerun()

# --- TELA: FORMAÇÃO CONTINUADA ---
elif menu == "🎓 Formação Continuada":
    st.title("🎓 Centro de Treinamento")
    treinos = carregar_dados(TREINAMENTOS_FILE)
    
    if not treinos: st.info("Nenhum treinamento disponível no momento.")
    
    for idx, t in enumerate(treinos):
        with st.expander(f"📺 MÓDULO: {t['titulo']}"):
            st.video(t['video_path'])
            st.divider()
            st.subheader("📝 Prova de Avaliação")
            
            respostas_agente = {}
            for q_idx, q in enumerate(t['questoes']):
                respostas_agente[q_idx] = st.radio(f"{q_idx+1}. {q['pergunta']}", q['opcoes'], key=f"q_{idx}_{q_idx}")
            
            if st.button("Enviar Avaliação", key=f"btn_p_{idx}"):
                acertos = sum(1 for q_idx, q in enumerate(t['questoes']) if respostas_agente[q_idx] == q['correta'])
                nota = (acertos / len(t['questoes'])) * 10
                notas = carregar_dados(NOTAS_FILE)
                notas.append({"usuario": st.session_state.user_logado, "treinamento": t['titulo'], "nota": nota, "data": datetime.now().strftime("%d/%m/%Y %H:%M")})
                salvar_dados(notas, NOTAS_FILE)
                if nota >= 7: st.success(f"Aprovado! Nota: {nota}")
                else: st.error(f"Nota: {nota}. Assista ao vídeo novamente para melhorar seu desempenho.")

# --- TELA: GESTÃO & REPORTS ---
elif menu == "📊 Gestão & Reports":
    if e_gestor:
        t_feed, t_aula, t_rep = st.tabs(["📢 Novo Comunicado", "🎓 Criar Treinamento", "📉 Relatórios Detalhados"])
        
        with t_feed:
            st.subheader("Publicar no Feed")
            msg_feed = st.text_area("Texto do comunicado")
            img_feed = st.file_uploader("Upload de imagem (Opcional)", type=['png', 'jpg', 'jpeg'])
            if st.button("Enviar para a Operação"):
                img_b64 = f"data:image/png;base64,{base64.b64encode(img_feed.read()).decode()}" if img_feed else None
                f = carregar_dados(FEED_FILE)
                f.insert(0, {"id": datetime.now().strftime("%Y%m%d%H%M%S"), "data": datetime.now().strftime("%d/%m/%Y %H:%M"), "msg": msg_feed, "img": img_b64, "curtidas_usuarios": [], "comentarios": []})
                salvar_dados(f, FEED_FILE); st.success("Comunicado publicado!"); st.rerun()

        with t_aula:
            st.subheader("Configurar Novo Módulo")
            titulo_aula = st.text_input("Nome do Treinamento")
            video_aula = st.file_uploader("Upload do Arquivo de Vídeo", type=['mp4', 'mov', 'avi'])
            
            if 'temp_perguntas' not in st.session_state: st.session_state.temp_perguntas = []
            
            st.info(f"Questões adicionadas: {len(st.session_state.temp_perguntas)}")
            with st.container():
                p_txt = st.text_input("Pergunta da Prova")
                c1, c2, c3 = st.columns(3)
                opA = c1.text_input("Opção A")
                opB = c2.text_input("Opção B")
                opC = c3.text_input("Opção C")
                correta = st.selectbox("Alternativa Correta", [opA, opB, opC])
                
                if st.button("➕ Adicionar Pergunta à Prova"):
                    if p_txt and opA:
                        st.session_state.temp_perguntas.append({"pergunta": p_txt, "opcoes": [opA, opB, opC], "correta": correta})
                        st.rerun()

            if st.button("💾 SALVAR TREINAMENTO COMPLETO"):
                if titulo_aula and video_aula and st.session_state.temp_perguntas:
                    path = os.path.join(VIDEO_DIR, video_aula.name)
                    with open(path, "wb") as f: f.write(video_aula.getbuffer())
                    
                    dados_t = carregar_dados(TREINAMENTOS_FILE)
                    dados_t.append({"titulo": titulo_aula, "video_path": path, "questoes": st.session_state.temp_perguntas})
                    salvar_dados(dados_t, TREINAMENTOS_FILE)
                    st.session_state.temp_perguntas = []
                    st.success("Módulo de treinamento criado com sucesso!"); st.rerun()

        with t_rep:
            st.subheader("📊 Engajamento do Feed (Logs de Interação)")
            feed_raw = carregar_dados(FEED_FILE)
            logs = []
            for p in feed_raw:
                resumo = p.get('msg', '')[:40] + "..."
                for u_lk in p.get('curtidas_usuarios', []):
                    logs.append({"Data": p.get('data'), "Post": resumo, "Usuário": u_lk, "Ação": "Curtiu ❤️"})
                for com in p.get('comentarios', []):
                    logs.append({"Data": com.get('data'), "Post": resumo, "Usuário": com.get('user'), "Ação": f"Comentou: {com.get('txt')}"})
            
            if logs:
                df_logs = pd.DataFrame(logs)
                st.dataframe(df_logs, use_container_width=True)
                st.download_button("Baixar Logs de Interação", df_logs.to_csv(index=False), "logs_interacao.csv")
            
            st.divider()
            st.subheader("📝 Notas das Avaliações")
            df_notas = pd.DataFrame(carregar_dados(NOTAS_FILE))
            if not df_notas.empty:
                st.dataframe(df_notas, use_container_width=True)
                st.download_button("Baixar Notas (CSV)", df_notas.to_csv(index=False), "notas_treinamento.csv")
    else:
        st.error("Acesso restrito ao time de Gestão.")
    
