import { useState, useRef } from "react";
import axios from "axios";

const API = axios.create({
  baseURL: "/api",
});

export default function Chat() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const formRef = useRef(null);

  async function handleSubmit(e) {
    e.preventDefault();
    const question = input.trim();
    if (!question || loading) return;

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
      formRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }

  return (
    <div className="page">
      <h2>Chat</h2>
      <p className="subtitle">Ask questions about your customers</p>

      <div className="chat-history">
        {messages.map((msg, i) => (
          <div key={i} className={`chat-bubble ${msg.role}`}>
            {msg.text}
          </div>
        ))}
        {loading && <div className="chat-bubble assistant">Thinking...</div>}
      </div>

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
