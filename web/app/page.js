"use client";

import { useRef, useState } from "react";

const suggestions = [
  ["Orders & delivery", "How can I track my order?", "↗"],
  ["Returns & refunds", "What is your return policy?", "↩"],
  ["Account help", "How can I reset my password?", "◯"],
];

function Sources({ sources }) {
  if (!sources?.length) return null;
  return (
    <details className="sources">
      <summary>▣ &nbsp; View {sources.length} supporting FAQ{sources.length === 1 ? "" : "s"}</summary>
      <div className="source-list">
        {sources.map((source) => (
          <article key={`${source.documentId}-${source.question}`}>
            <strong>{source.question}</strong>
            <p>{source.answer}</p>
            <small>{source.category.replaceAll("_", " ")} · {source.documentId} · Similarity {source.similarity.toFixed(3)}</small>
          </article>
        ))}
        <p className="similarity-note">Similarity measures the retrieval match, not answer accuracy.</p>
      </div>
    </details>
  );
}

export default function Home() {
  const [screen, setScreen] = useState("welcome");
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const inputRef = useRef(null);

  async function ask(text) {
    const clean = text.trim();
    if (!clean || loading) return;
    setScreen("chat");
    setQuestion("");
    setMessages((current) => [...current, { role: "user", text: clean }]);
    setLoading(true);
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: clean }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || "The assistant could not answer.");
      setMessages((current) => [...current, {
        role: "assistant",
        text: payload.answer,
        sources: payload.sources || [],
      }]);
    } catch (error) {
      setMessages((current) => [...current, {
        role: "assistant",
        text: error.message,
        error: true,
      }]);
    } finally {
      setLoading(false);
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }

  function submit(event) {
    event.preventDefault();
    ask(question);
  }

  return (
    <main>
      <header className="brand"><span>✦</span> northstar <i>/</i> <small>customer care</small></header>
      <section className="messenger">
        <header className="toolbar">
          <button aria-label="Back to welcome" onClick={() => setScreen("welcome")} disabled={screen === "welcome" || loading}>←</button>
          <div><strong>Northstar support</strong><span>Your AI shopping assistant</span></div>
          <button aria-label="Clear conversation" onClick={() => setMessages([])} disabled={loading}>↻</button>
        </header>

        {screen === "welcome" ? (
          <div className="welcome">
            <div className="welcome-copy">
              <small>A LITTLE HELP, RIGHT HERE</small>
              <h1>Hello there <span>✳</span></h1>
              <p>Good questions deserve helpful answers.<br />What can we help you with today?</p>
            </div>
            <div className="presence">
              <div className="avatar">✦</div>
              <strong>Meet your Northstar assistant</strong>
              <span>Help with the little things, and the next steps.</span>
              <small>✧ &nbsp; AI-powered support</small>
            </div>
            <div className="start-card">
              <h2>Let’s talk</h2>
              <p>Ask a question. We’ll find a place to start.</p>
              <button onClick={() => setScreen("chat")}>{messages.length ? "Continue conversation" : "Start a conversation"}<span>→</span></button>
            </div>
            <div className="topics"><small>OR EXPLORE A TOPIC</small>
              {suggestions.map(([label, text, icon]) => <button key={label} onClick={() => ask(text)}><span>{icon}</span>{label}<b>→</b></button>)}
            </div>
          </div>
        ) : (
          <>
            <div className="conversation">
              <div className="date-label">YOUR CONVERSATION</div>
              <div className="message assistant"><label>Northstar assistant</label><div className="bubble">Hi! I can help with orders, returns, payments, and your account. How can I help?</div></div>
              {messages.map((message, index) => (
                <div className={`message ${message.role}`} key={index}>
                  <label>{message.role === "user" ? "You" : "Northstar assistant"}</label>
                  <div className={`bubble ${message.error ? "error" : ""}`}>{message.text}</div>
                  <Sources sources={message.sources} />
                </div>
              ))}
              {loading && <div className="thinking"><i></i><i></i><i></i><span>Finding an answer for you…</span></div>}
            </div>
            <form className="composer" onSubmit={submit}>
              <input ref={inputRef} value={question} onChange={(event) => setQuestion(event.target.value)} disabled={loading} maxLength={1000} placeholder="Ask a question…" aria-label="Ask a question" />
              <button disabled={loading || !question.trim()} aria-label="Send question">↑</button>
              <small>AI can make mistakes. Check the supporting FAQs.</small>
            </form>
          </>
        )}
      </section>
      <footer>✧ &nbsp; Powered by the Northstar help library<br /><small>Portfolio demo · Fictional shop · 2,000 synthetic FAQ phrasings</small></footer>
    </main>
  );
}
