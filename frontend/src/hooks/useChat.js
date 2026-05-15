import { useState, useCallback } from "react";
import { queryDocument } from "../api/client";

/**
 * Manages chat conversation state against the currently loaded PDF.
 *
 * @returns {{
 *   messages: Array<{id: number, role: 'user'|'assistant', content: string, sources?: Array, isError?: boolean}>,
 *   isLoading: boolean,
 *   sendQuestion: (question: string) => Promise<void>,
 *   clearMessages: () => void
 * }}
 */
export function useChat() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const sendQuestion = useCallback(async (question) => {
    const userMessage = {
      id: Date.now(),
      role: "user",
      content: question,
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await queryDocument(question);
      const assistantMessage = {
        id: Date.now(),
        role: "assistant",
        content: response.answer,
        sources: response.sources,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage = {
        id: Date.now(),
        role: "assistant",
        content: error.message,
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return { messages, isLoading, sendQuestion, clearMessages };
}
