// ---------------------------------------------------------------------------
// CHAT PAGE
// ---------------------------------------------------------------------------
// Provides an interactive Q&A interface for asking natural language
// questions about customer data. Each question and answer is displayed
// as chat bubbles in a scrollable history.

import { useState, useRef } from "react";
import axios from "axios";

// Create a dedicated axios instance for the chat API.
// Base URL is /api (proxied by Vite dev server or nginx to the backend).
const API = axios.create({
  baseURL: "/api",
});

export default function Chat() {
  // input   — the current text in the input field
  // messages— array of { role, text } objects for the chat history
  // loading — true while waiting for the API response
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  // formRef is attached to the form element so we can scroll it into view
  // after each response (auto-scroll to the input field).
  const formRef = useRef(null);

  // Handle form submission: send the question to POST /chat
  async function handleSubmit(e) {
    e.preventDefault();
    const question = input.trim();
    if (!question || loading) return;

    // Add user's message to the chat history
    const userMsg = { role: "user", text: question };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const { data } = await API.post("/chat", { question });
      const botMsg = {
        role: "assistant",
        text: data.answer || data.error || "No response.",
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: `Error: ${err.message}` },
      ]);
    } finally {
      setLoading(false);
      // Auto-scroll to the input form so the user can type the next question
      formRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }

  return (
    <div className="page">
      <h2>Chat</h2>
      <p className="subtitle">Ask questions about your customers</p>

      {/* Chat history — renders all messages as bubbles */}
      <div className="chat-history">
        {messages.map((msg, i) => (
          <div key={i} className={`chat-bubble ${msg.role}`}>
            {msg.text}
          </div>
        ))}
        {loading && <div className="chat-bubble assistant">Thinking...</div>}
      </div>

      {/* Input form — fixed at the bottom of the page */}
      <form ref={formRef} className="chat-form" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question..."
          className="chat-input"
        />
        <button type="submit" className="chat-button" disabled={loading}>
          Send
        </button>
      </form>
    </div>
  );
}
