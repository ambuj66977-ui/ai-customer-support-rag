"""Exercise messenger navigation and recovery without loading ML models."""

from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from src.rag_pipeline import FALLBACK_ANSWER, RAGResult
from src.retriever import RetrievalResult


APP = Path(__file__).resolve().parents[1] / "app.py"


def button(app, label):
    return next(item for item in app.button if item.label == label)


def test_conversation_sources_navigation_and_clear():
    source = RetrievalResult("FAQ-1", "How can I track my order?", "Use your order page.", "orders", "track", .8, 1)
    result = RAGResult(source.question, source.answer, [source], False)
    with patch("src.embeddings.SentenceTransformerEmbedder"), patch(
        "src.retriever.FaissRetriever.from_directory"
    ), patch("src.rag_pipeline.RAGPipeline.ask", return_value=result) as ask:
        app = AppTest.from_file(str(APP)).run()
        button(app, "Orders & delivery").click().run()
        assert not app.exception
        assert len(app.session_state.messages) == 2
        assert any(item.label == "View 1 supporting FAQs" for item in [*app.expander, *app.status])
        button(app, "Back to welcome").click().run()
        button(app, "Continue conversation").click().run()
        assert len(app.session_state.messages) == 2
        assert ask.call_count == 1
        button(app, "Clear conversation").click().run()
        assert app.session_state.messages == []
        assert not app.exception


def test_failure_retries_without_duplicating_user_message():
    result = RAGResult("How can I track my order?", "Use your order page.", [], False)
    with patch("src.embeddings.SentenceTransformerEmbedder"), patch(
        "src.retriever.FaissRetriever.from_directory"
    ), patch("src.rag_pipeline.RAGPipeline.ask", side_effect=[RuntimeError("private details"), result]):
        app = AppTest.from_file(str(APP)).run()
        button(app, "Orders & delivery").click().run()
        assert app.session_state.messages[-1]["error"]
        assert "private details" not in app.session_state.messages[-1]["text"]
        button(app, "Try again").click().run()
        assert len(app.session_state.messages) == 2
        assert app.session_state.messages[-1]["text"] == result.answer
        assert not app.exception


def test_typed_question_fallback_and_html_escaping():
    question = "<script>alert('hello')</script>"
    with patch("src.embeddings.SentenceTransformerEmbedder"), patch(
        "src.retriever.FaissRetriever.from_directory"
    ), patch("src.rag_pipeline.RAGPipeline.ask", return_value=RAGResult(question, FALLBACK_ANSWER, [], True)):
        app = AppTest.from_file(str(APP)).run()
        button(app, "Start a conversation").click().run()
        app.chat_input[0].set_value(question).run()
        assert app.session_state.messages[-1]["text"] == FALLBACK_ANSWER
        assert not app.expander
        assert any("&lt;script&gt;" in item.value for item in app.markdown)
        assert not app.exception
