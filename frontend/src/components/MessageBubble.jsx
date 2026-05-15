import ReactMarkdown from "react-markdown";
import SourceBadge from "./SourceBadge";
import "./components.css";

/**
 * Renders a single chat message bubble.
 *
 * @param {{
 *   message: {
 *     role: 'user'|'assistant',
 *     content: string,
 *     sources?: Array<{ source_file: string, page_numbers: number[] }>,
 *     isError?: boolean
 *   }
 * }} props
 */
export default function MessageBubble({ message }) {
  const { role, content, sources, isError } = message;
  const isUser = role === "user";

  let bubbleClass = "message-bubble";
  if (isUser) {
    bubbleClass += " message-bubble--user";
  } else if (isError) {
    bubbleClass += " message-bubble--assistant message-bubble--error";
  } else {
    bubbleClass += " message-bubble--assistant";
  }

  return (
    <div className={bubbleClass}>
      <div className="message-bubble__content">
        {isUser ? (
          content
        ) : (
          <ReactMarkdown>{content}</ReactMarkdown>
        )}
      </div>

      {!isUser && !isError && sources && sources.length > 0 && (
        <div className="message-bubble__sources">
          {sources.map((source, index) => (
            <SourceBadge key={index} source={source} />
          ))}
        </div>
      )}
    </div>
  );
}
