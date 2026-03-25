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
        st.image("data:image/jpeg;base64,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", width=250)
        u = st.text_input("Usuário")
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
st.sidebar.image("https://www.mideacarrier.com.br/wp-content/themes/midea-carrier/assets/img/logo-midea-carrier.png", width=120)
st.sidebar.markdown(f"👤 **Bem-vindo, {st.session_state.user_logado}**")
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
    
