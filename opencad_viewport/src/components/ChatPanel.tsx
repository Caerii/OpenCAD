import { useState } from "react";
import type { ChatOperationExecution } from "../types";

interface ChatPanelProps {
  onSend: (message: string, reasoning: boolean) => Promise<{
    response: string;
    operations: ChatOperationExecution[];
  }>;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

export function ChatPanel({ onSend }: ChatPanelProps): JSX.Element {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [operations, setOperations] = useState<ChatOperationExecution[]>([]);
  const [input, setInput] = useState("");
  const [reasoning, setReasoning] = useState(false);
  const [pending, setPending] = useState(false);

  const submit = async () => {
    const message = input.trim();
    if (!message || pending) {
      return;
    }

    setPending(true);
    setInput("");
    setMessages((current) => [...current, { role: "user", content: message }]);
    setOperations([]);

    const result = await onSend(message, reasoning);

    const assistantMessage: ChatMessage = { role: "assistant", content: "" };
    setMessages((current) => [...current, assistantMessage]);

    let stream = "";
    for (const ch of result.response) {
      stream += ch;
      setMessages((current) => {
        const next = [...current];
        next[next.length - 1] = { role: "assistant", content: stream };
        return next;
      });
      await sleep(9);
    }

    const shown: ChatOperationExecution[] = [];
    for (const operation of result.operations) {
      shown.push(operation);
      setOperations([...shown]);
      await sleep(170);
    }

    setPending(false);
  };

  return (
    <section className="chat-panel">
      <header className="chat-header">
        <h3>AI Chat</h3>
        <label className="reasoning-toggle">
          <input
            type="checkbox"
            checked={reasoning}
            onChange={(event) => setReasoning(event.target.checked)}
          />
          High Reasoning
        </label>
      </header>

      <div className="chat-messages">
        {messages.map((message, index) => (
          <div key={`${message.role}-${index}`} className={`chat-message ${message.role}`}>
            <strong>{message.role === "user" ? "You" : "Agent"}</strong>
            <p>{message.content}</p>
          </div>
        ))}
      </div>

      <div className="chat-ops">
        {operations.map((operation, index) => (
          <div key={`${operation.tool}-${index}`} className="chat-op-row">
            <span className={`op-status ${operation.status}`}>{operation.status}</span>
            <span className="op-tool">{operation.tool}</span>
            <code>{JSON.stringify(operation.arguments)}</code>
          </div>
        ))}
      </div>

      <div className="chat-input-row">
        <input
          type="text"
          value={input}
          placeholder="Describe a feature to build"
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              void submit();
            }
          }}
        />
        <button type="button" onClick={() => void submit()} disabled={pending}>
          {pending ? "Running..." : "Send"}
        </button>
      </div>
    </section>
  );
}
