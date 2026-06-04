import { useMemo, useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';

import { createTestChatCompletion, type TestChatResponse } from './chat-client';
import { useAuth } from './auth';

type TranscriptItem = {
  id: string;
  sender: 'user' | 'assistant';
  content: string;
};

function createTranscriptId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function formatLabel(value: string): string {
  return value
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

export function TestChatPage() {
  const { user } = useAuth();
  const [draft, setDraft] = useState('');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [transcript, setTranscript] = useState<TranscriptItem[]>([]);
  const [latestResponse, setLatestResponse] = useState<TestChatResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);

  const canSubmit = draft.trim().length > 0 && !isSending;
  const persistenceStatus = useMemo(() => {
    if (!latestResponse) {
      return null;
    }
    return typeof latestResponse.metadata.persistence_status === 'string'
      ? latestResponse.metadata.persistence_status
      : null;
  }, [latestResponse]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextMessage = draft.trim();
    if (!nextMessage) {
      return;
    }

    setIsSending(true);
    setErrorMessage(null);

    try {
      const response = await createTestChatCompletion({
        conversation_id: conversationId,
        message: nextMessage,
        display_name: user?.display_name,
      });
      setTranscript((current) => [
        ...current,
        { id: createTranscriptId('user'), sender: 'user', content: nextMessage },
        {
          id: createTranscriptId(`assistant-${response.message_id}`),
          sender: 'assistant',
          content: response.reply.content,
        },
      ]);
      setConversationId(response.conversation_id);
      setLatestResponse(response);
      setDraft('');
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : 'Test chat request failed.',
      );
    } finally {
      setIsSending(false);
    }
  }

  function handleReset() {
    setDraft('');
    setConversationId(null);
    setTranscript([]);
    setLatestResponse(null);
    setErrorMessage(null);
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <p className="eyebrow">Experience loop</p>
        <h2>Test Chat</h2>
        <p>
          Send a real request to <code>/api/v1/chat</code>, keep the returned
          <code> conversation_id</code>, and jump to the persisted conversation detail
          for backend inspection.
        </p>
      </div>

      <div className="test-chat-layout">
        <section className="test-chat-panel">
          <form className="test-chat-composer" onSubmit={handleSubmit}>
            <label className="field">
              <span>Message</span>
              <textarea
                name="message"
                onChange={(event) => setDraft(event.target.value)}
                placeholder="例如：帮我查一下 EVER GIVEN 当前船位"
                rows={5}
                value={draft}
              />
            </label>
            {errorMessage ? (
              <p className="form-error detail-inline-feedback" role="alert">
                {errorMessage}
              </p>
            ) : null}
            <div className="test-chat-actions">
              <button className="primary-button" disabled={!canSubmit} type="submit">
                {isSending ? 'Sending...' : 'Send test message'}
              </button>
              <button className="secondary-button" onClick={handleReset} type="button">
                Reset session
              </button>
              {conversationId ? (
                <Link
                  className="secondary-button"
                  to={`/conversations/${encodeURIComponent(conversationId)}`}
                >
                  Open persisted conversation
                </Link>
              ) : null}
            </div>
          </form>

          <div className="test-chat-transcript">
            {transcript.length > 0 ? (
              transcript.map((item) => (
                <article
                  className={`test-chat-message test-chat-message-${item.sender}`}
                  key={item.id}
                >
                  <strong>{item.sender === 'user' ? 'User' : 'Assistant'}</strong>
                  <p>{item.content}</p>
                </article>
              ))
            ) : (
              <section className="loading-panel empty-panel">
                <h4>No messages yet</h4>
                <p>Start a test chat here, then inspect the same conversation in the backend.</p>
              </section>
            )}
          </div>
        </section>

        <aside className="test-chat-sidebar">
          <section className="panel detail-section-panel">
            <div className="panel-header">
              <p className="eyebrow">Runtime</p>
              <h3>Latest response</h3>
            </div>
            <dl className="detail-meta-grid">
              <div>
                <dt>Conversation ID</dt>
                <dd>{conversationId ?? 'Not started'}</dd>
              </div>
              <div>
                <dt>Handoff status</dt>
                <dd>{latestResponse ? formatLabel(latestResponse.handoff_status) : 'N/A'}</dd>
              </div>
              <div>
                <dt>Persistence</dt>
                <dd>{persistenceStatus ? formatLabel(persistenceStatus) : 'N/A'}</dd>
              </div>
            </dl>
          </section>

          <section className="panel detail-section-panel">
            <div className="panel-header">
              <p className="eyebrow">Artifacts</p>
              <h3>Tool calls and sources</h3>
            </div>
            {latestResponse && latestResponse.tool_calls.length > 0 ? (
              <div className="detail-list-stack">
                {latestResponse.tool_calls.map((toolCall) => (
                  <article className="detail-list-item" key={toolCall.tool_name}>
                    <div className="detail-list-item-header">
                      <strong>{toolCall.tool_name}</strong>
                      <span className="status-pill muted-pill">
                        {formatLabel(toolCall.status)}
                      </span>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <p className="test-chat-muted">No tool calls in the latest response.</p>
            )}

            {latestResponse && latestResponse.sources.length > 0 ? (
              <div className="detail-list-stack">
                {latestResponse.sources.map((source) => (
                  <article
                    className="detail-list-item note-item"
                    key={`${source.source_type}-${source.title}`}
                  >
                    <strong>{source.title}</strong>
                    <p>{source.snippet}</p>
                  </article>
                ))}
              </div>
            ) : (
              <p className="test-chat-muted">No cited sources in the latest response.</p>
            )}
          </section>
        </aside>
      </div>
    </section>
  );
}
