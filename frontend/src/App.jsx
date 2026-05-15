import { useSession } from "./hooks/useSession";
import { useChat } from "./hooks/useChat";
import UploadPanel from "./components/UploadPanel";
import ChatPanel from "./components/ChatPanel";
import "./App.css";

export default function App() {
  const { filename, uploadStatus, uploadError, uploadFile } = useSession();
  const { messages, isLoading, sendQuestion, clearMessages } = useChat();

  const hasSession = uploadStatus === "success" || filename !== null;

  return (
    <div className="app">
      {/* Header */}
      <header className="app__header">
        <h1 className="app__title">AI Second Brain</h1>
        {hasSession && filename ? (
          <span className="app__active-file" title={filename}>
            📄 {filename}
          </span>
        ) : (
          <span className="app__no-file">Upload a PDF to get started</span>
        )}
      </header>

      {/* Main two-column layout */}
      <main className="app__body">
        <section className="app__left" aria-label="Upload">
          <UploadPanel
            filename={filename}
            uploadStatus={uploadStatus}
            uploadError={uploadError}
            uploadFile={uploadFile}
            onUploadSuccess={clearMessages}
          />
        </section>

        <section className="app__right" aria-label="Chat">
          <ChatPanel
            messages={messages}
            isLoading={isLoading}
            sendQuestion={sendQuestion}
            hasSession={hasSession}
          />
        </section>
      </main>
    </div>
  );
}
