"""
Agent de Planification de Voyage Autonome
Interface Streamlit avec ReAct + CoT + Streaming
"""

import streamlit as st
import sys
import os
import json
import time
import re
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Charger le fichier .env si présent (compatible Windows/Linux/macOS)
try:
    from dotenv import load_dotenv
    env_path = Path(os.path.dirname(os.path.abspath(__file__))) / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    pass  # python-dotenv non installé, on continue avec les variables d'environnement système

from agent_engine import stream_agent_response, SYSTEM_PROMPT
from tools.itinerary_tool import get_current_itinerary
from utils.pdf_exporter import export_itinerary_to_pdf
from utils.email_sender import send_itinerary_email, SMTP_PRESETS

# ─────────────────────────────────────────────────────────────
# Configuration de la page Streamlit
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Agent Planificateur de Voyage",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────
# CSS personnalisé
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Palette de couleurs */
:root {
    --primary: #1a73e8;
    --primary-dark: #1557b0;
    --secondary: #34a853;
    --accent: #fbbc04;
    --danger: #ea4335;
    --bg-dark: #0f1117;
    --bg-card: #1e2130;
    --bg-card2: #252840;
    --text-main: #e8eaf6;
    --text-muted: #9fa8da;
    --border: #3949ab;
}

/* Corps principal */
.main .block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
    max-width: 1100px;
}

/* En-tête hero */
.hero-header {
    background: linear-gradient(135deg, #1a237e 0%, #1565c0 50%, #0288d1 100%);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px rgba(26, 35, 126, 0.4);
    border: 1px solid rgba(255,255,255,0.1);
}
.hero-header h1 {
    color: #ffffff;
    font-size: 2rem;
    font-weight: 800;
    margin: 0 0 0.3rem 0;
    text-shadow: 0 2px 8px rgba(0,0,0,0.3);
}
.hero-header p {
    color: rgba(255,255,255,0.85);
    font-size: 1rem;
    margin: 0;
}

/* Badge technique */
.tech-badge {
    display: inline-block;
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.75rem;
    color: #ffffff;
    margin: 0.3rem 0.2rem 0 0;
    font-weight: 600;
}

/* Bulles de message */
.msg-user {
    background: linear-gradient(135deg, #1a73e8, #1557b0);
    color: white;
    border-radius: 18px 18px 4px 18px;
    padding: 1rem 1.2rem;
    margin: 0.8rem 0 0.8rem 3rem;
    box-shadow: 0 4px 12px rgba(26, 115, 232, 0.3);
    font-size: 0.95rem;
    line-height: 1.5;
}
.msg-assistant {
    background: #1e2130;
    border: 1px solid #3949ab;
    color: #e8eaf6;
    border-radius: 18px 18px 18px 4px;
    padding: 1rem 1.2rem;
    margin: 0.8rem 3rem 0.8rem 0;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    font-size: 0.95rem;
    line-height: 1.6;
}

/* Boîte de raisonnement ReAct */
.react-box {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border: 1px solid #4a4a8a;
    border-left: 4px solid #7c4dff;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin: 0.5rem 0;
    font-family: 'Courier New', monospace;
    font-size: 0.82rem;
    color: #b39ddb;
}
.react-box .react-label {
    color: #7c4dff;
    font-weight: bold;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.3rem;
}

/* Boîte d'outil appelé */
.tool-box {
    background: linear-gradient(135deg, #0a1628, #0d2137);
    border: 1px solid #1565c0;
    border-left: 4px solid #29b6f6;
    border-radius: 8px;
    padding: 0.7rem 1rem;
    margin: 0.4rem 0;
    font-size: 0.85rem;
    color: #81d4fa;
}
.tool-box .tool-name {
    color: #29b6f6;
    font-weight: bold;
    font-family: monospace;
}
.tool-box .tool-args {
    color: #4fc3f7;
    font-family: monospace;
    font-size: 0.78rem;
    margin-top: 0.2rem;
}

/* Boîte de résultat d'outil */
.tool-result-box {
    background: linear-gradient(135deg, #0a1f0a, #0d2b0d);
    border: 1px solid #2e7d32;
    border-left: 4px solid #66bb6a;
    border-radius: 8px;
    padding: 0.5rem 1rem;
    margin: 0.3rem 0;
    font-size: 0.8rem;
    color: #a5d6a7;
}

/* Indicateur de progression */
.progress-step {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 0.8rem;
    border-radius: 6px;
    margin: 0.2rem 0;
    font-size: 0.85rem;
}
.step-done { background: rgba(52, 168, 83, 0.15); color: #66bb6a; }
.step-active { background: rgba(26, 115, 232, 0.15); color: #64b5f6; }
.step-pending { background: rgba(255,255,255,0.05); color: #9e9e9e; }

/* Boutons d'action */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
}

/* Input de chat */
.stChatInput > div {
    border-radius: 12px !important;
    border: 2px solid #3949ab !important;
}
.stChatInput > div:focus-within {
    border-color: #1a73e8 !important;
    box-shadow: 0 0 0 3px rgba(26, 115, 232, 0.2) !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f1117 0%, #1a1a2e 100%);
    border-right: 1px solid #3949ab;
}

/* Cards de stats */
.stat-card {
    background: #1e2130;
    border: 1px solid #3949ab;
    border-radius: 10px;
    padding: 0.8rem 1rem;
    text-align: center;
    margin: 0.3rem 0;
}
.stat-card .stat-value {
    font-size: 1.5rem;
    font-weight: 800;
    color: #1a73e8;
}
.stat-card .stat-label {
    font-size: 0.75rem;
    color: #9fa8da;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Suggestions rapides */
.suggestion-btn {
    background: rgba(26, 115, 232, 0.1);
    border: 1px solid rgba(26, 115, 232, 0.3);
    border-radius: 20px;
    padding: 0.4rem 0.9rem;
    font-size: 0.82rem;
    color: #90caf9;
    cursor: pointer;
    transition: all 0.2s;
    display: inline-block;
    margin: 0.2rem;
}
.suggestion-btn:hover {
    background: rgba(26, 115, 232, 0.25);
    border-color: #1a73e8;
}

/* Alerte météo */
.weather-alert {
    background: rgba(251, 188, 4, 0.1);
    border: 1px solid rgba(251, 188, 4, 0.4);
    border-radius: 8px;
    padding: 0.6rem 1rem;
    color: #fdd835;
    font-size: 0.85rem;
    margin: 0.5rem 0;
}

/* Export section */
.export-section {
    background: linear-gradient(135deg, #1e2130, #252840);
    border: 1px solid #3949ab;
    border-radius: 12px;
    padding: 1.2rem;
    margin-top: 1rem;
}

/* Scrollbar personnalisée */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0f1117; }
::-webkit-scrollbar-thumb { background: #3949ab; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #1a73e8; }

/* Masquer les éléments Streamlit par défaut */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Initialisation du state
# ─────────────────────────────────────────────────────────────
def init_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "itinerary_ready" not in st.session_state:
        st.session_state.itinerary_ready = False
    if "tool_calls_count" not in st.session_state:
        st.session_state.tool_calls_count = 0
    if "trips_planned" not in st.session_state:
        st.session_state.trips_planned = 0
    if "show_react_trace" not in st.session_state:
        st.session_state.show_react_trace = True
    if "current_destination" not in st.session_state:
        st.session_state.current_destination = ""
    if "pending_input" not in st.session_state:
        st.session_state.pending_input = None
    if "show_email_form" not in st.session_state:
        st.session_state.show_email_form = False
    if "email_smtp_preset" not in st.session_state:
        st.session_state.email_smtp_preset = "gmail"

init_state()


# ─────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0 0.5rem 0;">
        <div style="font-size: 3rem;">✈️</div>
        <div style="font-size: 1.1rem; font-weight: 800; color: #e8eaf6;">Travel Agent AI</div>
        <div style="font-size: 0.75rem; color: #9fa8da; margin-top: 0.2rem;">Powered by ReAct + CoT</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Statistiques de session
    st.markdown("**📊 Session en cours**")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{st.session_state.trips_planned}</div>
            <div class="stat-label">Voyages</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{st.session_state.tool_calls_count}</div>
            <div class="stat-label">Outils</div>
        </div>""", unsafe_allow_html=True)

    st.divider()

    # Options d'affichage
    st.markdown("**⚙️ Options d'affichage**")
    st.session_state.show_react_trace = st.toggle(
        "Afficher le raisonnement ReAct",
        value=st.session_state.show_react_trace,
        help="Visualise les étapes de raisonnement Thought → Action → Observation"
    )

    st.divider()

    # Destinations suggérées
    st.markdown("**🌍 Destinations populaires**")
    destinations = [
        ("🇲🇾", "Malaisie", "Je veux aller en Malaisie au mois de septembre"),
        ("🇹🇭", "Thaïlande", "Planifie un voyage en Thaïlande en décembre"),
        ("🇯🇵", "Japon", "Je voudrais visiter le Japon en avril pour les cerisiers"),
        ("🇲🇦", "Maroc", "Organise un voyage au Maroc en octobre"),
        ("🇮🇩", "Bali", "Je veux partir à Bali en juillet"),
        ("🇮🇹", "Italie", "Planifie un voyage en Italie en mai"),
    ]

    for flag, name, prompt in destinations:
        if st.button(f"{flag} {name}", key=f"dest_{name}", use_container_width=True):
            st.session_state.pending_input = prompt
            st.rerun()

    st.divider()

    # Bouton reset
    if st.button("🔄 Nouvelle conversation", use_container_width=True, type="secondary"):
        for key in ["messages", "chat_history", "itinerary_ready",
                    "tool_calls_count", "trips_planned", "current_destination", "pending_input"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    st.divider()

    # Info technique
    st.markdown("""
    <div style="font-size: 0.72rem; color: #5c6bc0; text-align: center; line-height: 1.6;">
        <strong style="color: #7986cb;">Architecture</strong><br>
        🧠 ReAct (Reason + Act)<br>
        💭 Chain-of-Thought (CoT)<br>
        ⚡ Streaming temps réel<br>
        🔧 5 outils spécialisés<br>
        📄 Export PDF intégré
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Zone principale
# ─────────────────────────────────────────────────────────────

# En-tête hero
st.markdown("""
<div class="hero-header">
    <h1>✈️ Agent Planificateur de Voyage Autonome</h1>
    <p>Décrivez votre voyage en langage naturel — l'agent s'occupe de tout : météo, vols, hôtels, restaurants et itinéraire complet.</p>
    <div>
        <span class="tech-badge">🧠 ReAct</span>
        <span class="tech-badge">💭 Chain-of-Thought</span>
        <span class="tech-badge">⚡ Streaming</span>
        <span class="tech-badge">🔧 Multi-Outils</span>
        <span class="tech-badge">📄 Export PDF</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# Affichage de l'historique du chat
# ─────────────────────────────────────────────────────────────
chat_container = st.container()

with chat_container:
    if not st.session_state.chat_history:
        # Message de bienvenue
        st.markdown("""
        <div style="text-align: center; padding: 3rem 1rem; color: #9fa8da;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">🌍</div>
            <div style="font-size: 1.2rem; font-weight: 600; color: #e8eaf6; margin-bottom: 0.5rem;">
                Où souhaitez-vous voyager ?
            </div>
            <div style="font-size: 0.9rem; margin-bottom: 1.5rem;">
                Dites-moi simplement votre destination et la période — même approximative !
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Exemples de requêtes
        st.markdown("""
        <div style="text-align: center; margin-bottom: 1rem;">
            <div style="font-size: 0.8rem; color: #5c6bc0; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 1px;">
                Exemples de requêtes
            </div>
        </div>
        """, unsafe_allow_html=True)

        examples = [
            "Je veux aller en Malaisie au mois de septembre",
            "Planifie un voyage au Japon en avril pour voir les cerisiers",
            "Organise un séjour de 10 jours au Maroc en mai avec un budget moyen",
            "Je voudrais visiter la Thaïlande en décembre, quelles sont les meilleures périodes ?",
        ]

        cols = st.columns(2)
        for i, ex in enumerate(examples):
            with cols[i % 2]:
                if st.button(f"💬 {ex}", key=f"ex_{i}", use_container_width=True):
                    st.session_state.pending_input = ex
                    st.rerun()
    else:
        # Afficher l'historique
        for entry in st.session_state.chat_history:
            if entry["role"] == "user":
                st.markdown(f"""
                <div class="msg-user">
                    <strong>👤 Vous</strong><br>{entry["content"]}
                </div>
                """, unsafe_allow_html=True)
            elif entry["role"] == "assistant":
                with st.container():
                    # Trace ReAct si activée
                    if st.session_state.show_react_trace and entry.get("react_trace"):
                        with st.expander("🧠 Trace ReAct — Raisonnement de l'agent", expanded=False):
                            for trace_item in entry["react_trace"]:
                                if trace_item["type"] == "tool_call":
                                    args_str = json.dumps(trace_item["args"], ensure_ascii=False, indent=2)
                                    st.markdown(f"""
                                    <div class="tool-box">
                                        <div class="tool-name">⚙️ ACTION → {trace_item['tool']}</div>
                                        <div class="tool-args">{args_str}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                elif trace_item["type"] == "tool_result":
                                    preview = trace_item["result"][:200] + "..." if len(trace_item["result"]) > 200 else trace_item["result"]
                                    st.markdown(f"""
                                    <div class="tool-result-box">
                                        ✅ OBSERVATION ← {trace_item['tool']}<br>
                                        <span style="font-size:0.75rem;">{preview}</span>
                                    </div>
                                    """, unsafe_allow_html=True)

                    # Réponse principale
                    st.markdown(f"""
                    <div class="msg-assistant">
                        <strong>🤖 Agent Voyage</strong><br>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(entry["content"])


# ─────────────────────────────────────────────────────────────
# Formulaire d'envoi email SMTP
# ─────────────────────────────────────────────────────────────
def _render_email_form():
    """Affiche le formulaire de configuration SMTP et d'envoi d'email."""
    itinerary = get_current_itinerary()
    if not itinerary["content"]:
        st.warning("⚠️ Aucun itinéraire disponible. Générez d'abord un voyage.")
        return

    st.markdown("""
    <div style="background:linear-gradient(135deg,#0d1b2a,#1a2744);
                border:1px solid #3949ab; border-radius:14px;
                padding:1.4rem 1.6rem; margin:1rem 0;">
        <div style="font-size:1rem; font-weight:700; color:#90caf9; margin-bottom:0.3rem;">
            📧 Envoyer l'itinéraire par email
        </div>
        <div style="font-size:0.82rem; color:#7986cb;">
            Le PDF sera généré automatiquement et joint à l'email.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Sélection du fournisseur SMTP ────────────────────────────
    preset_labels = {k: v["label"] for k, v in SMTP_PRESETS.items()}
    preset_key = st.selectbox(
        "🌐 Fournisseur de messagerie",
        options=list(preset_labels.keys()),
        format_func=lambda k: preset_labels[k],
        key="smtp_preset_select"
    )
    preset = SMTP_PRESETS[preset_key]

    # Note d'aide spécifique au fournisseur
    st.info(f"💡 {preset['note']}")

    # ── Champs du formulaire ────────────────────────────────
    col_a, col_b = st.columns(2)
    with col_a:
        recipient = st.text_input(
            "📨 Email destinataire",
            placeholder="exemple@gmail.com",
            key="email_recipient"
        )
    with col_b:
        sender = st.text_input(
            "📤 Votre email (expéditeur)",
            value=os.getenv("SMTP_SENDER_EMAIL", ""),
            placeholder="votre.email@gmail.com",
            key="email_sender_field"
        )

    password = st.text_input(
        "🔑 Mot de passe SMTP (ou App Password)",
        type="password",
        value=os.getenv("SMTP_PASSWORD", ""),
        placeholder="Votre mot de passe d'application",
        key="email_password"
    )

    # Champs avancés pour SMTP custom
    if preset_key == "custom":
        col_c, col_d = st.columns(2)
        with col_c:
            custom_host = st.text_input(
                "🌐 Serveur SMTP (host)",
                placeholder="smtp.monserveur.com",
                key="smtp_custom_host"
            )
        with col_d:
            custom_port = st.number_input(
                "🔌 Port SMTP",
                value=587, min_value=1, max_value=65535,
                key="smtp_custom_port"
            )
        smtp_host = custom_host
        smtp_port = int(custom_port)
    else:
        smtp_host = preset["host"]
        smtp_port = preset["port"]

    # ── Bouton d'envoi ─────────────────────────────────────
    col_send, col_cancel = st.columns([2, 1])
    with col_send:
        send_clicked = st.button(
            "🚀 Envoyer l'itinéraire maintenant",
            type="primary", use_container_width=True,
            key="send_email_confirm"
        )
    with col_cancel:
        if st.button("❌ Annuler", use_container_width=True, key="cancel_email"):
            st.session_state.show_email_form = False
            st.rerun()

    if send_clicked:
        # Validation rapide
        if not recipient or "@" not in recipient:
            st.error("❌ Veuillez saisir une adresse email destinataire valide.")
            return
        if not sender or "@" not in sender:
            st.error("❌ Veuillez saisir votre adresse email expéditeur.")
            return
        if not password:
            st.error("❌ Veuillez saisir votre mot de passe SMTP.")
            return

        with st.spinner("📤 Génération du PDF et envoi en cours..."):
            # 1. Générer le PDF
            pdf_path = None
            try:
                pdf_path = export_itinerary_to_pdf(
                    content=itinerary["content"],
                    destination=itinerary["destination"],
                    month=itinerary["month"]
                )
            except Exception as pdf_err:
                st.warning(f"⚠️ PDF non généré ({pdf_err}), l'email sera envoyé sans pièce jointe.")

            # 2. Envoyer l'email
            result = send_itinerary_email(
                recipient_email=recipient,
                destination=itinerary["destination"],
                month=itinerary["month"],
                itinerary_text=itinerary["content"],
                pdf_path=pdf_path,
                sender_email=sender,
                sender_password=password,
                smtp_host=smtp_host,
                smtp_port=smtp_port,
                use_tls=preset.get("use_tls", True)
            )

        if result["success"]:
            st.success(f"✅ {result['message']}")
            st.balloons()
            st.session_state.show_email_form = False
        else:
            st.error(f"❌ {result['message']}")


# ─────────────────────────────────────────────────────────────
# Section Export (si itinéraire disponible)
# ─────────────────────────────────────────────────────────────
if st.session_state.itinerary_ready:
    st.markdown("""
    <div class="export-section">
        <div style="font-size: 1rem; font-weight: 700; color: #e8eaf6; margin-bottom: 0.8rem;">
            📥 Votre itinéraire est prêt !
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("📄 Télécharger en PDF", type="primary", use_container_width=True, key="dl_pdf_top"):
            itinerary = get_current_itinerary()
            if itinerary["content"]:
                with st.spinner("Génération du PDF..."):
                    try:
                        pdf_path = export_itinerary_to_pdf(
                            content=itinerary["content"],
                            destination=itinerary["destination"],
                            month=itinerary["month"]
                        )
                        with open(pdf_path, "rb") as f:
                            pdf_bytes = f.read()
                        dest_clean = itinerary["destination"].replace(" ", "_").lower()
                        st.download_button(
                            label="⬇️ Cliquez pour télécharger",
                            data=pdf_bytes,
                            file_name=f"itineraire_{dest_clean}_{itinerary['month']}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            key="dl_pdf_top_btn"
                        )
                        st.success("✅ PDF généré avec succès !")
                    except Exception as e:
                        st.error(f"Erreur PDF : {str(e)}")

    with col2:
        if st.button("📧 Envoyer par Email", use_container_width=True, key="email_btn_top"):
            st.session_state.show_email_form = not st.session_state.show_email_form
            st.rerun()

    with col3:
        if st.button("✏️ Modifier l'itinéraire", use_container_width=True, key="modify_btn_top"):
            st.info("💬 Utilisez le chat ci-dessous pour modifier votre itinéraire !")

    # ── Formulaire d'envoi email (affiché/masqué par toggle) ──────
    if st.session_state.show_email_form:
        _render_email_form()


# ─────────────────────────────────────────────────────────────
# Zone de saisie du chat
# ─────────────────────────────────────────────────────────────
st.divider()

# Traiter l'input en attente (depuis sidebar ou exemples)
if st.session_state.pending_input:
    user_input = st.session_state.pending_input
    st.session_state.pending_input = None
else:
    user_input = st.chat_input(
        "Décrivez votre voyage... (ex: 'Je veux aller en Malaisie en septembre')",
        key="chat_input"
    )

# ─────────────────────────────────────────────────────────────
# Traitement de la requête utilisateur
# ─────────────────────────────────────────────────────────────
if user_input:
    # Ajouter le message utilisateur à l'historique
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_input
    })
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    # Extraire la destination pour les stats
    dest_keywords = ["malaisie", "thaïlande", "japon", "maroc", "bali", "france",
                     "italie", "espagne", "grèce", "vietnam", "cambodge", "indonésie"]
    for kw in dest_keywords:
        if kw in user_input.lower():
            st.session_state.current_destination = kw.title()
            break

    # Afficher le message utilisateur immédiatement
    st.markdown(f"""
    <div class="msg-user">
        <strong>👤 Vous</strong><br>{user_input}
    </div>
    """, unsafe_allow_html=True)

    # Zone de streaming de la réponse
    react_trace = []
    response_placeholder = st.empty()
    status_placeholder = st.empty()

    # Indicateur de progression ReAct
    steps = [
        ("🌤️", "Analyse météo & climat"),
        ("✈️", "Recherche transports"),
        ("🏨", "Recherche hébergements"),
        ("🍽️", "Recommandations restauration"),
        ("📅", "Construction itinéraire"),
    ]
    current_step = [0]
    full_response_text = [""]
    streaming_text = [""]

    def on_thought(token: str):
        """Callback pour le streaming du texte."""
        streaming_text[0] += token
        # Afficher le texte en streaming
        response_placeholder.markdown(
            f'<div class="msg-assistant"><strong>🤖 Agent Voyage</strong><br>{streaming_text[0]}▌</div>',
            unsafe_allow_html=True
        )

    def on_tool_call(tool_name: str, tool_args: dict):
        """Callback quand l'agent appelle un outil."""
        st.session_state.tool_calls_count += 1
        react_trace.append({
            "type": "tool_call",
            "tool": tool_name,
            "args": tool_args
        })

        # Mapper l'outil à l'étape
        tool_step_map = {
            "get_weather_info": 0,
            "search_flights": 1,
            "search_hotels": 2,
            "search_restaurants": 3,
            "build_itinerary": 4
        }
        step_idx = tool_step_map.get(tool_name, current_step[0])
        current_step[0] = step_idx

        # Afficher la progression
        if st.session_state.show_react_trace:
            args_preview = ", ".join([f"{k}={v}" for k, v in list(tool_args.items())[:2]])
            status_placeholder.markdown(f"""
            <div class="tool-box">
                <div class="tool-name">⚙️ ACTION → {tool_name}({args_preview})</div>
                <div class="tool-args">Appel de l'outil en cours...</div>
            </div>
            """, unsafe_allow_html=True)

    def on_tool_result(tool_name: str, result: str):
        """Callback après l'exécution d'un outil."""
        react_trace.append({
            "type": "tool_result",
            "tool": tool_name,
            "result": result
        })

        if st.session_state.show_react_trace:
            preview = result[:150] + "..." if len(result) > 150 else result
            status_placeholder.markdown(f"""
            <div class="tool-result-box">
                ✅ OBSERVATION ← {tool_name} terminé
                <br><span style="font-size:0.75rem;">{preview}</span>
            </div>
            """, unsafe_allow_html=True)

        # Détecter si l'itinéraire est prêt
        if tool_name == "build_itinerary":
            st.session_state.itinerary_ready = True
            st.session_state.trips_planned += 1

    # Lancer l'agent
    with st.spinner(""):
        try:
            final_response = stream_agent_response(
                messages=st.session_state.messages,
                on_thought=on_thought,
                on_tool_call=on_tool_call,
                on_tool_result=on_tool_result
            )
        except Exception as e:
            final_response = f"Une erreur s'est produite : {str(e)}\n\nVeuillez réessayer ou reformuler votre demande."

    # Nettoyer les placeholders
    status_placeholder.empty()
    response_placeholder.empty()

    # Afficher la réponse finale
    st.markdown(f"""
    <div class="msg-assistant">
        <strong>🤖 Agent Voyage</strong><br>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(final_response)

    # Sauvegarder dans l'historique
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": final_response,
        "react_trace": react_trace
    })

    # Afficher la trace ReAct si disponible
    if st.session_state.show_react_trace and react_trace:
        with st.expander("🧠 Trace ReAct — Voir le raisonnement de l'agent", expanded=False):
            for trace_item in react_trace:
                if trace_item["type"] == "tool_call":
                    args_str = json.dumps(trace_item["args"], ensure_ascii=False, indent=2)
                    st.markdown(f"""
                    <div class="tool-box">
                        <div class="tool-name">⚙️ ACTION → {trace_item['tool']}</div>
                        <div class="tool-args">{args_str}</div>
                    </div>
                    """, unsafe_allow_html=True)
                elif trace_item["type"] == "tool_result":
                    preview = trace_item["result"][:300] + "..." if len(trace_item["result"]) > 300 else trace_item["result"]
                    st.markdown(f"""
                    <div class="tool-result-box">
                        ✅ OBSERVATION ← {trace_item['tool']}<br>
                        <span style="font-size:0.75rem;">{preview}</span>
                    </div>
                    """, unsafe_allow_html=True)

    # Afficher les boutons d'export si itinéraire prêt
    if st.session_state.itinerary_ready:
        st.markdown("""
        <div class="export-section">
            <div style="font-size: 1rem; font-weight: 700; color: #e8eaf6; margin-bottom: 0.8rem;">
                🎉 Itinéraire complet généré !
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("📄 Télécharger PDF", type="primary", use_container_width=True, key="dl_pdf_new"):
                itinerary = get_current_itinerary()
                if itinerary["content"]:
                    with st.spinner("Génération du PDF..."):
                        try:
                            pdf_path = export_itinerary_to_pdf(
                                content=itinerary["content"],
                                destination=itinerary["destination"],
                                month=itinerary["month"]
                            )
                            with open(pdf_path, "rb") as f:
                                pdf_bytes = f.read()
                            dest_clean = itinerary["destination"].replace(" ", "_").lower()
                            st.download_button(
                                label="⬇️ Télécharger l'itinéraire PDF",
                                data=pdf_bytes,
                                file_name=f"itineraire_{dest_clean}_{itinerary['month']}.pdf",
                                mime="application/pdf",
                                use_container_width=True,
                                key="download_pdf_btn"
                            )
                            st.success("✅ PDF prêt !")
                        except Exception as e:
                            st.error(f"Erreur : {str(e)}")

        with col2:
            if st.button("📧 Envoyer par Email", use_container_width=True, key="send_email_new"):
                st.session_state.pending_input = "Je voudrais recevoir l'itinéraire par email. Peux-tu me demander mon adresse email ?"
                st.rerun()

        with col3:
            if st.button("✏️ Modifier", use_container_width=True, key="modify_new"):
                st.info("💬 Dites-moi ce que vous souhaitez modifier dans le chat !")

    st.rerun()
