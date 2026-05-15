import { useState, useRef, useEffect } from "react";
import MessageBubble from "./MessageBubble";
import LoadingSpinner from "./LoadingSpinner";
import "./components.css";

/**
 * Chat panel — scrollable message history + question input.
 *
 * @param {{
 *   messages: Array<{ id: number, role: 'user'|'assistant', content: string, sources?: Array, isError?: boolean }>,
 *   isLoading: boolean,
 *   sendQuestion: (question: string) => Promise<void>,
 *   hasSession: boolean
 * }} props
 */
export default function ChatPanel({ messages, isLoading, sendQuestion, hasSession }) {
  const [input, setInput] = useState("");
  const [validationMsg, setValidationMsg] = useState("");
  const bottomRef = useRef(null);

  // Auto-scroll to the latest message
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isLoading]);

  function handleSubmit(e) {
    e.preventDefault();
    const question = input.trim();

    if (!question) {
      setValidationMsg("Please enter a question.");
      return;
    }

    setValidationMsg("");
    setInput("");
    sendQuestion(question);
  }

  const inputDisabled = !hasSession || isLoading;

  return (
    <div className="chat-panel">
      {/* Message list */}
      <div className="chat-panel__messages">
        {messages.length === 0 && !hasSession && (
          <p className="chat-panel__placeholder">Upload a PDF to start chatting.</p>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {/* Loading indicator while waiting for assistant response */}
        {isLoading && (
          <div className="chat-panel__loading-row">
            <LoadingSpinner small />
            <span>Thinking…</span>
          </div>
        )}

        {/* Scroll anchor */}
        <div ref={bottomRef} />
      </div>

      {/* Input footer */}
      <div className="chat-panel__footer">
        <form className="chat-panel__input-row" onSubmit={handleSubmit}>
          <input
            className="chat-panel__input"
            type="text"
            placeholder={hasSession ? "Ask a question…" : "Upload a PDF to start chatting."}
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              if (validationMsg) setValidationMsg("");
            }}
            disabled={inputDisabled}
            aria-label="Question input"
          />
          <button
            type="submit"
            className="chat-panel__send-btn"
            disabled={inputDisabled}
          >
            {isLoading ? <LoadingSpinner small /> : "Send"}
          </button>
        </form>

        {validationMsg && (
          <p className="chat-panel__validation-msg">{validationMsg}</p>
        )}
      </div>
    </div>
  );
}
