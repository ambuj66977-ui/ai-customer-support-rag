"use client";

import { useRef, useState } from "react";

const suggestions = [
  ["How do I track my order?", "How do I track my order?", "↗"],
  ["What is your return policy?", "What is your return policy?", "↩"],
  ["When will my refund arrive?", "When will my refund arrive?", "◷"],
];

function Sources({ sources }) {
  if (!sources?.length) return null;
  return (
    <details className="sources">
      <summary>▣ &nbsp; Related help articles ({sources.length})</summary>
      <div className="source-list">
        {sources.map((source) => (
          <article key={`${source.documentId}-${source.question}`}>
            <strong>{source.question}</strong>
            <p>{source.answer}</p>
            <small>Northstar Help Center · {source.category.replaceAll("_", " ")}</small>
          </article>
        ))}
        <p className="similarity-note">These articles explain the policies used in this answer.</p>
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
      if (!response.ok) throw new Error(payload.error || "We couldn’t get an answer right now. Please try again.");
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
      <header className="brand"><span>✦</span> northstar shop <i>/</i> <small>customer care</small></header>
      <section className="messenger">
        <header className="toolbar">
          <button aria-label="Back to welcome" onClick={() => setScreen("welcome")} disabled={screen === "welcome" || loading}>←</button>
          <div><strong>Northstar Shop Support</strong><span>Help with your shopping, every step</span></div>
          <button aria-label="Clear conversation" onClick={() => setMessages([])} disabled={loading}>↻</button>
        </header>

        {screen === "welcome" ? (
          <div className="welcome">
            <div className="welcome-copy">
              <small>WELCOME TO NORTHSTAR SHOP</small>
              <h1>Here to help. <span>✳</span></h1>
              <p>We’re an online store for everyday products and accessories.<br />Get help before you buy, while your order is on its way, or after it arrives.</p>
            </div>
            <div className="presence">
              <div className="avatar">✦</div>
              <strong>Your shopping questions, answered</strong>
              <span>Delivery · Returns · Refunds · Payments · Account help</span>
              <small>✧ &nbsp; AI support from the Northstar Help Center</small>
            </div>
            <div className="start-card">
              <h2>How can we help?</h2>
              <p>Ask about an order, check our returns policy, or get help with a payment.</p>
              <button onClick={() => setScreen("chat")}>{messages.length ? "Continue your conversation" : "Start a conversation"}<span>→</span></button>
            </div>
            <div className="topics"><small>POPULAR QUESTIONS</small>
              {suggestions.map(([label, text, icon]) => <button key={label} onClick={() => ask(text)}><span>{icon}</span>{label}<b>→</b></button>)}
            </div>
          </div>
        ) : (
          <>
            <div className="conversation">
              <div className="date-label">NORTHSTAR SHOP HELP CENTER</div>
              <div className="message assistant"><label>Northstar AI assistant</label><div className="bubble">Hi! I’m Northstar Shop’s AI support assistant. We’re an online store for everyday products and accessories. Ask about delivery, returns, refunds, payments, or your account. I can explain our policies and next steps, but can’t access or change individual orders.</div></div>
              {messages.map((message, index) => (
                <div className={`message ${message.role}`} key={index}>
                  <label>{message.role === "user" ? "You" : "Northstar AI assistant"}</label>
                  <div className={`bubble ${message.error ? "error" : ""}`}>{message.text}</div>
                  <Sources sources={message.sources} />
                </div>
              ))}
              {loading && <div className="thinking"><i></i><i></i><i></i><span>Checking our help center…</span></div>}
            </div>
            <form className="composer" onSubmit={submit}>
              <input ref={inputRef} value={question} onChange={(event) => setQuestion(event.target.value)} disabled={loading} maxLength={1000} placeholder="Ask about orders or returns…" aria-label="Ask Northstar Shop a support question" />
              <button disabled={loading || !question.trim()} aria-label="Send question">↑</button>
              <small>AI-assisted support · Answers based on our help center.</small>
            </form>
          </>
        )}
      </section>
      <footer>✧ &nbsp; Northstar Shop · Customer care<br /><small>Here to help with your shopping.</small></footer>
    </main>
  );
}
