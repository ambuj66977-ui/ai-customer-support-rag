"use client";

import { useRef, useState } from "react";

const suggestions = [
  ["How do I track my order?", "How do I track my order?", "package"],
  ["What is your return policy?", "What is your return policy?", "return"],
  ["When will my refund arrive?", "When will my refund arrive?", "receipt"],
];

function BrandMark({ className = "" }) {
  return <svg className={"brand-mark " + className} width="48" height="48" viewBox="0 0 48 48" fill="none" aria-hidden="true"><path d="M7 39V9h8l18 22V9h8v30h-8L15 17v22H7Z" fill="currentColor" /><path d="m33 4 4-4 4 4" stroke="currentColor" strokeWidth="2.5" strokeLinecap="square" strokeLinejoin="miter" /></svg>;
}

function Icon({ name, className = "" }) {
  const paths = {
    back: <path d="m14 6-6 6 6 6M8 12h12" />,
    package: <><path d="m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3Z" /><path d="m4 7.5 8 4.5 8-4.5M12 12v9M8 5.25l8 4.5" /></>,
    return: <><path d="m8 5-5 5 5 5M3 10h11a6 6 0 0 1 0 12" transform="translate(1 -2)" /></>,
    receipt: <><path d="M6 3h12v18l-3-2-3 2-3-2-3 2V3Z" /><path d="M9 7h6M9 11h6M9 15h3" /></>,
    article: <><path d="M7 4h13v16H7zM4 7v13a3 3 0 0 0 3 3h10" /><path d="M10 8h7M10 12h7M10 16h4" /></>,
    chevron: <path d="m9 5 7 7-7 7" />,
    arrow: <path d="M4 12h16m-6-6 6 6-6 6" />,
    clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
  };
  return <svg className={className} width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>;
}

function Sources({ sources }) {
  if (!sources?.length) return null;
  return (
    <details className="sources">
      <summary><Icon name="article" /><span>Related help articles ({sources.length})</span><Icon name="chevron" className="disclosure-icon" /></summary>
      <div className="source-list">
        {sources.map((source) => (
          <article key={source.documentId + "-" + source.question}>
            <strong>{source.question}</strong>
            <p>{source.answer}</p>
            <small>Northstar Help Center: {source.category.replaceAll("_", " ")}</small>
          </article>
        ))}
        <p className="source-note">These articles explain the policies used in this answer.</p>
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
      <header className="site-header">
        <div className="brand"><BrandMark /><div className="wordmark">northstar<span>shop</span></div></div>
        <div className="header-note"><span>Everyday products. Everyday support.</span><strong>Customer care <Icon name="arrow" /></strong></div>
      </header>
      <section className={"messenger " + (screen === "chat" ? "is-chat" : "")} aria-label="Northstar Shop support">
        <header className="toolbar">
          <button type="button" aria-label="Back to welcome" onClick={() => setScreen("welcome")} disabled={screen === "welcome" || loading}><Icon name="back" /><span>Back</span></button>
          <div className="toolbar-title"><strong>Help center</strong><span>Northstar Shop Support</span></div>
          <button type="button" aria-label="Clear conversation" onClick={() => setMessages([])} disabled={loading}>Clear chat</button>
        </header>
        {screen === "welcome" ? (
          <div className="welcome">
            <div className="welcome-copy">
              <p className="welcome-label"><span className="brand-dot" />Welcome to Northstar customer care</p>
              <h1>Good shopping.<br /><span>Great support.</span></h1>
              <p className="store-intro">We’re an online store for everyday products and accessories.</p>
              <p className="support-intro">Get help before you buy, while your order is on its way, or after it arrives.</p>
              <div className="start-card">
                <button type="button" className="primary-button" onClick={() => setScreen("chat")}>{messages.length ? "Continue your conversation" : "Start a conversation"}<Icon name="arrow" /></button>
                <p>Ask about an order, check our returns policy, or get help with a payment.</p>
              </div>
            </div>
            <div className="help-index">
              <div className="help-index-heading"><BrandMark /><span>The Northstar<br />help desk</span></div>
              <div className="topics">
                <h2>Let’s get it sorted.</h2>
                <p className="topics-intro">Pick a question. We’ll take it from here.</p>
                {suggestions.map(([label, text, icon]) => (
                  <button type="button" key={label} onClick={() => ask(text)}><Icon name={icon} /><span>{label}</span><Icon name="chevron" className="topic-chevron" /></button>
                ))}
              </div>
              <div className="presence">
                <Icon name="article" /><p>Answers from our help center.<br /><span>Delivery, returns, payments and more.</span></p>
              </div>
            </div>
          </div>
        ) : (
          <div className="chat-workspace">
            <div className="conversation" role="log" aria-live="polite" aria-label="Your conversation">
              <div className="conversation-heading"><BrandMark /><div><h1 className="conversation-title">Let’s talk.</h1><p>Your Northstar shopping questions, answered.</p></div></div>
              <div className="message assistant"><label>Northstar AI assistant</label><div className="bubble">Hi! I’m Northstar Shop’s AI support assistant. We’re an online store for everyday products and accessories. Ask about delivery, returns, refunds, payments, or your account. I can explain our policies and next steps, but can’t access or change individual orders.</div></div>
              {messages.map((message, index) => (
                <div className={"message " + message.role} key={index}>
                  <label>{message.role === "user" ? "You" : "Northstar AI assistant"}</label>
                  <div className={"bubble " + (message.error ? "error" : "")}>{message.text}</div>
                  <Sources sources={message.sources} />
                </div>
              ))}
              {loading && <div className="thinking" role="status"><Icon name="clock" /><span>Checking our help center…</span></div>}
            </div>
            <form className="composer" onSubmit={submit} aria-busy={loading}>
              <label htmlFor="support-question">Your question</label>
              <div className="composer-row">
                <input id="support-question" name="question" type="text" autoComplete="off" required ref={inputRef} value={question} onChange={(event) => setQuestion(event.target.value)} disabled={loading} maxLength={1000} placeholder="When will my refund arrive?" aria-label="Ask Northstar Shop a support question" aria-describedby="support-help" />
                <button type="submit" className="primary-button" disabled={loading} aria-label="Send question">{loading ? "Sending…" : "Send"}</button>
              </div>
              <small id="support-help">AI-assisted support. Answers based on our help center.</small>
            </form>
          </div>
        )}
      </section>
      <footer><div className="footer-brand"><BrandMark /><span>northstar shop</span></div><span>Everyday shopping. A little less complicated.</span><span>AI-assisted customer care</span></footer>
    </main>
  );
}
