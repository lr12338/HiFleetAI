import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { useAuth } from './auth';
import {
  fetchConversationDetail,
  type ConversationDetail,
  type ConversationDetailMessage,
  type ConversationErrorItem,
  type ConversationToolCallSummary,
} from './conversations-client';

function formatTimestamp(value: string | null): string {
  if (!value) {
    return 'Not available';
  }

  const parsedDate = new Date(value);
  if (Number.isNaN(parsedDate.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(parsedDate);
}

function formatLabel(value: string): string {
  return value
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function formatJsonBlock(value: Record<string, unknown> | null): string {
  if (!value || Object.keys(value).length === 0) {
    return 'No structured metadata recorded.';
  }

  return JSON.stringify(value, null, 2);
}

function DetailMetaItem({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="detail-meta-item">
      <dt>{label}</dt>
      <dd className={mono ? 'conversation-id' : undefined}>{value}</dd>
    </div>
  );
}

function TimelineItem({ message }: { message: ConversationDetailMessage }) {
  const payloadText = useMemo(() => {
    if (!message.content_payload) {
      return null;
    }

    return JSON.stringify(message.content_payload, null, 2);
  }, [message.content_payload]);

  return (
    <article className="timeline-item">
      <div className="timeline-item-header">
        <div>
          <h4>{formatLabel(message.sender_type)}</h4>
          <p>
            {formatLabel(message.message_type)} · {formatLabel(message.send_status)}
          </p>
        </div>
        <time dateTime={message.created_at}>{formatTimestamp(message.created_at)}</time>
      </div>
      {message.content ? (
        <p className="timeline-item-content">{message.content}</p>
      ) : (
        <p className="timeline-item-empty">No text content recorded for this message.</p>
      )}
      {payloadText ? <pre className="json-block">{payloadText}</pre> : null}
    </article>
  );
}

function ToolCallItem({ toolCall }: { toolCall: ConversationToolCallSummary }) {
  return (
    <article className="detail-list-item">
      <div className="detail-list-item-header">
        <h4>{toolCall.tool_name}</h4>
        <span className="status-pill muted-pill">{formatLabel(toolCall.status)}</span>
      </div>
      <dl className="detail-inline-list">
        <div>
          <dt>Created</dt>
          <dd>{formatTimestamp(toolCall.created_at)}</dd>
        </div>
        <div>
          <dt>Latency</dt>
          <dd>{toolCall.latency_ms === null ? 'Not recorded' : `${toolCall.latency_ms} ms`}</dd>
        </div>
        <div>
          <dt>Message ID</dt>
          <dd className="conversation-id">{toolCall.message_id ?? 'Not linked'}</dd>
        </div>
      </dl>
      {toolCall.error_message ? (
        <p className="detail-inline-error">{toolCall.error_message}</p>
      ) : null}
    </article>
  );
}

function ErrorItem({ error }: { error: ConversationErrorItem }) {
  return (
    <article className="detail-list-item error-item">
      <div className="detail-list-item-header">
        <h4>
          {formatLabel(error.source)}
          {error.tool_name ? ` · ${error.tool_name}` : ''}
        </h4>
        <span className="status-pill error-pill">{formatLabel(error.code)}</span>
      </div>
      <p className="timeline-item-content">
        {error.message ?? 'No error message was recorded.'}
      </p>
      <dl className="detail-inline-list">
        <div>
          <dt>Created</dt>
          <dd>{formatTimestamp(error.created_at)}</dd>
        </div>
        <div>
          <dt>Message ID</dt>
          <dd className="conversation-id">{error.message_id ?? 'Not linked'}</dd>
        </div>
        <div>
          <dt>Error ID</dt>
          <dd className="conversation-id">{error.id}</dd>
        </div>
      </dl>
    </article>
  );
}

export function ConversationDetailPage() {
  const { token } = useAuth();
  const { conversationId } = useParams();
  const [detail, setDetail] = useState<ConversationDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [requestVersion, setRequestVersion] = useState(0);

  useEffect(() => {
    if (!token || !conversationId) {
      setDetail(null);
      setIsLoading(false);
      setErrorMessage('Conversation detail route is missing an id.');
      return;
    }

    let cancelled = false;
    setIsLoading(true);
    setErrorMessage(null);

    void fetchConversationDetail(token, conversationId)
      .then((response) => {
        if (!cancelled) {
          setDetail(response);
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setDetail(null);
          setErrorMessage(
            error instanceof Error
              ? error.message
              : 'Unable to load conversation detail.',
          );
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [conversationId, requestVersion, token]);

  function handleRetry() {
    setRequestVersion((current) => current + 1);
  }

  if (isLoading) {
    return (
      <section className="panel">
        <div className="panel-header">
          <p className="eyebrow">Conversation detail</p>
          <h2>Loading conversation detail...</h2>
          <p>The console is fetching the latest timeline, tool calls, and error context.</p>
        </div>
      </section>
    );
  }

  if (errorMessage || !detail) {
    return (
      <section className="panel">
        <div className="panel-header detail-header">
          <div>
            <p className="eyebrow">Conversation detail</p>
            <h2>Unable to load conversation</h2>
            <p>The requested conversation detail could not be rendered.</p>
          </div>
          <Link className="secondary-button" to="/">
            Back to conversations
          </Link>
        </div>
        <div className="form-error conversation-feedback" role="alert">
          <div>
            <strong>Conversation detail request failed.</strong>
            <p>{errorMessage ?? 'No detail data was returned by the API.'}</p>
          </div>
          <button className="secondary-button" onClick={handleRetry} type="button">
            Retry
          </button>
        </div>
      </section>
    );
  }

  const errorItems = [
    ...detail.error_context.model_errors,
    ...detail.error_context.tool_errors,
  ];

  return (
    <section className="detail-page">
      <div className="panel detail-hero">
        <div className="panel-header detail-header">
          <div>
            <p className="eyebrow">Conversation detail</p>
            <h2>{detail.title ?? 'Untitled conversation'}</h2>
            <p>
              Review the minimal detail contract returned by the protected conversation
              detail API.
            </p>
          </div>
          <div className="detail-header-actions">
            <span className="status-pill">{formatLabel(detail.status)}</span>
            <span className="status-pill muted-pill">
              {formatLabel(detail.handoff_status)}
            </span>
            <Link className="secondary-button" to="/">
              Back to conversations
            </Link>
          </div>
        </div>

        <div className="detail-grid">
          <div className="detail-section">
            <h3>Conversation overview</h3>
            <dl className="detail-meta-grid">
              <DetailMetaItem label="Conversation ID" value={detail.id} mono />
              <DetailMetaItem label="User ID" value={detail.user_id ?? 'Not linked'} mono />
              <DetailMetaItem label="Channel" value={formatLabel(detail.channel_type)} />
              <DetailMetaItem
                label="Assigned agent"
                value={detail.assigned_agent_id ?? 'Unassigned'}
                mono
              />
              <DetailMetaItem
                label="Last activity"
                value={formatTimestamp(detail.last_message_at)}
              />
              <DetailMetaItem label="Created" value={formatTimestamp(detail.created_at)} />
              <DetailMetaItem label="Updated" value={formatTimestamp(detail.updated_at)} />
            </dl>
            <div className="detail-summary-block">
              <h4>Summary</h4>
              <p>
                {detail.summary ?? 'No summary has been generated for this conversation yet.'}
              </p>
            </div>
            <div className="detail-summary-block">
              <h4>Metadata</h4>
              <pre className="json-block">{formatJsonBlock(detail.metadata)}</pre>
            </div>
          </div>
        </div>
      </div>

      <div className="detail-content-grid">
        <section className="panel detail-section-panel">
          <div className="panel-header">
            <p className="eyebrow">Timeline</p>
            <h3>Message timeline</h3>
            <p>Messages are rendered in API order so operators can replay the interaction.</p>
          </div>
          {detail.messages.length > 0 ? (
            <div className="timeline-list">
              {detail.messages.map((message) => (
                <TimelineItem key={message.id} message={message} />
              ))}
            </div>
          ) : (
            <section className="loading-panel empty-panel">
              <h4>No messages recorded</h4>
              <p>This conversation does not contain any persisted messages yet.</p>
            </section>
          )}
        </section>

        <section className="panel detail-section-panel">
          <div className="panel-header">
            <p className="eyebrow">Tools</p>
            <h3>Tool call summary</h3>
            <p>Only the minimal per-call status and latency fields are shown in this MVP view.</p>
          </div>
          {detail.tool_calls.length > 0 ? (
            <div className="detail-list-stack">
              {detail.tool_calls.map((toolCall) => (
                <ToolCallItem key={toolCall.id} toolCall={toolCall} />
              ))}
            </div>
          ) : (
            <section className="loading-panel empty-panel">
              <h4>No tool calls recorded</h4>
              <p>The backend returned an empty tool-call summary for this conversation.</p>
            </section>
          )}
        </section>

        <section className="panel detail-section-panel">
          <div className="panel-header">
            <p className="eyebrow">Errors</p>
            <h3>Error context</h3>
            <p>Failed model calls and failed tool calls are grouped into one readable block.</p>
          </div>
          {errorItems.length > 0 ? (
            <div className="detail-list-stack">
              {errorItems.map((error) => (
                <ErrorItem key={`${error.source}-${error.id}`} error={error} />
              ))}
            </div>
          ) : (
            <section className="loading-panel empty-panel">
              <h4>No error context recorded</h4>
              <p>This conversation currently has no persisted model or tool failures.</p>
            </section>
          )}
        </section>
      </div>
    </section>
  );
}
