"""Northstar's support messenger, powered by the existing RAG pipeline."""

from __future__ import annotations

import logging
from html import escape
from pathlib import Path

import streamlit as st

from src.config import settings
from src.embeddings import SentenceTransformerEmbedder
from src.llm import LLMConfigurationError, create_language_model
from src.rag_pipeline import RAGPipeline
from src.retriever import FaissRetriever


st.set_page_config(page_title="Northstar · Customer care", page_icon="✦", layout="centered")
logger = logging.getLogger(__name__)
STYLES = Path(__file__).parent / "assets" / "support.css"
SUGGESTIONS = (
    ("Orders & delivery", "How can I track my order?", ":material/local_shipping:"),
    ("Returns & refunds", "What is your return policy?", ":material/assignment_return:"),
    ("Account help", "How can I reset my password?", ":material/person:"),
)


@st.cache_resource
def load_retriever() -> FaissRetriever:
    embedder = SentenceTransformerEmbedder(settings.embedding_model)
    return FaissRetriever.from_directory(settings.index_directory, embedder)


@st.cache_resource
def load_language_model():
    return create_language_model(
        settings.llm_provider,
        openai_model=settings.llm_model,
        openai_api_key=settings.openai_api_key,
        local_model=settings.local_llm_model,
    )


class LazyLanguageModel:
    """Load the model only when retrieval finds enough context to answer."""

    def generate(self, messages):
        return load_language_model().generate(messages)


def open_chat(question: str | None = None) -> None:
    st.session_state.screen = "chat"
    if question:
        st.session_state.messages.append({"role": "user", "text": question})
        st.session_state.pending_question = question


def submit_question() -> None:
    question = (st.session_state.question or "").strip()
    if question:
        open_chat(question)


def start_over() -> None:
    st.session_state.messages = []
    st.session_state.pending_question = None


def retry_question() -> None:
    st.session_state.messages.pop()
    st.session_state.pending_question = st.session_state.messages[-1]["text"]


def render_message(message: dict) -> None:
    role = message["role"]
    label = "You" if role == "user" else "Northstar assistant"
    # Keep both user and model content out of the HTML markup.
    st.markdown(
        f'<div class="message {role}" role="group" aria-label="{label}">'
        f'<div class="message-label">{label}</div>'
        f'<div class="bubble">{escape(message["text"])}</div></div>',
        unsafe_allow_html=True,
    )
    sources = message.get("sources", [])
    if sources:
        with st.expander(f"View {len(sources)} supporting FAQs", icon=":material/library_books:"):
            for source in sources:
                st.markdown(f"**{source.question}**")
                st.write(source.answer)
                st.caption(f"{source.category} · {source.document_id} · Similarity {source.similarity:.3f}")
            st.caption("Similarity measures the match to your question, not answer accuracy.")
    if message.get("error"):
        st.button("Try again", key="retry", icon=":material/refresh:", on_click=retry_question)


def generate_answer(question: str, top_k: int, threshold: float) -> dict:
    try:
        pipeline = RAGPipeline(
            load_retriever(),
            LazyLanguageModel(),
            top_k=top_k,
            min_similarity=threshold,
            answer_from_top_source=settings.llm_provider == "local",
        )
        result = pipeline.ask(question)
        sources = result.retrieved_documents
        if settings.llm_provider == "local":
            sources = sources[:1]
        return {"role": "assistant", "text": result.answer, "sources": sources}
    except FileNotFoundError:
        logger.exception("Support knowledge base or model file is missing")
        message = "The support library isn't ready yet. Please try again once the app has been set up."
    except LLMConfigurationError:
        logger.exception("Support model configuration failed")
        message = "The assistant needs a configuration update before it can reply. Please try again later."
    except Exception:
        logger.exception("Support answer generation failed")
        message = "I couldn't finish that answer. Please try again in a moment."
    return {"role": "assistant", "text": message, "error": True}


st.session_state.setdefault("screen", "welcome")
st.session_state.setdefault("messages", [])
st.session_state.setdefault("pending_question", None)
st.markdown(f"<style>{STYLES.read_text()}</style>", unsafe_allow_html=True)
st.markdown('<div class="page-brand"><span>✦</span> northstar<span class="brand-divider">/</span><small>customer care</small></div>', unsafe_allow_html=True)

with st.container(key="messenger", border=False):
    with st.container(key="toolbar"):
        back, title, options = st.columns([1, 6, 1], vertical_alignment="center")
        with back:
            if st.session_state.screen == "chat":
                st.button("Back to welcome", icon=":material/arrow_back:", type="tertiary", key="back",
                          on_click=lambda: st.session_state.update(screen="welcome"),
                          disabled=bool(st.session_state.pending_question))
            else:
                st.markdown('<div class="small-mark">✦</div>', unsafe_allow_html=True)
        with title:
            st.markdown('<div class="toolbar-title">Northstar support<span>Your AI shopping assistant</span></div>', unsafe_allow_html=True)
        with options:
            with st.popover("Settings", icon=":material/tune:", type="tertiary", width="content"):
                st.markdown("**Chat settings**")
                st.caption("Tune how the assistant searches the demo FAQ library.")
                top_k = st.slider("FAQs to retrieve", 1, 5, settings.top_k)
                threshold = st.slider("Minimum similarity", 0.0, 1.0, float(settings.min_similarity), 0.01)
                st.caption("Similarity is not a confidence score.")
                st.button("Clear conversation", icon=":material/restart_alt:", on_click=start_over,
                          disabled=bool(st.session_state.pending_question))

    if st.session_state.screen == "welcome":
        with st.container(key="welcome"):
            st.markdown('''<div class="welcome-intro">
                <div class="eyebrow">A LITTLE HELP, RIGHT HERE</div>
                <h1>Hello there <span class="wave">✳</span></h1>
                <p>Good questions deserve helpful answers.<br>What can we help you with today?</p>
                </div>
                <div class="assistant-presence"><div class="assistant-orbit"><div class="assistant-avatar">✦</div></div>
                <strong>Meet your Northstar assistant</strong>
                <span>Help with the little things, and the next steps.</span>
                <div class="ai-pill">✧ &nbsp; AI-powered support</div></div>''', unsafe_allow_html=True)
            with st.container(key="start-card"):
                st.markdown("### Let’s talk")
                st.markdown('<p class="start-description">Ask a question. We’ll find a place to start.</p>', unsafe_allow_html=True)
                label = "Continue conversation" if st.session_state.messages else "Start a conversation"
                st.button(label, icon=":material/arrow_forward:", icon_position="right", type="primary", width="stretch", on_click=open_chat)
            st.markdown('<div class="topics-label">OR EXPLORE A TOPIC</div>', unsafe_allow_html=True)
            for label, question, icon in SUGGESTIONS:
                st.button(label, icon=icon, key=f"welcome_{label}", width="stretch", on_click=open_chat, args=(question,))
    else:
        with st.container(key="conversation", height=440, border=False, autoscroll=True):
            st.markdown('<div class="conversation-date">YOUR CONVERSATION</div>', unsafe_allow_html=True)
            render_message({"role": "assistant", "text": "Hi! I’m the Northstar AI assistant. I can help you find answers about orders, returns, payments, and your account. How can I help?"})
            for index, message in enumerate(st.session_state.messages):
                render_message({**message, "error": message.get("error") and index == len(st.session_state.messages) - 1})
            if not st.session_state.messages:
                with st.container(key="suggestions"):
                    st.caption("Try asking")
                    for label, question, _ in SUGGESTIONS[:2]:
                        st.button(question, key=f"chat_{label}", on_click=open_chat, args=(question,))
            pending = st.session_state.pending_question
            if pending:
                with st.container(key="thinking"):
                    st.markdown('<div class="typing" role="status" aria-label="Preparing an answer"><i></i><i></i><i></i><span>Finding an answer for you…</span></div>', unsafe_allow_html=True)
                    st.caption("The first reply can take around 30 seconds while the assistant warms up.")
        with st.container(key="composer"):
            st.chat_input("Ask a question…", key="question", max_chars=2000,
                          on_submit=submit_question, disabled=bool(st.session_state.pending_question))
            st.markdown('<div class="composer-note">AI can make mistakes. Check the supporting FAQs.</div>', unsafe_allow_html=True)

st.markdown('<div class="page-footnote">✧ &nbsp; Powered by the Northstar help library<br><span>Portfolio demo · Fictional shop · Synthetic FAQs</span></div>', unsafe_allow_html=True)

# Render the full interface, including the disabled composer, before model work.
if st.session_state.pending_question:
    response = generate_answer(st.session_state.pending_question, top_k, threshold)
    st.session_state.messages.append(response)
    st.session_state.pending_question = None
    st.rerun()
