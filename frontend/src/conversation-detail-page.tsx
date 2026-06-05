import { useEffect, useMemo, useState, type ChangeEvent, type FormEvent } from 'react';
import { Link, useParams } from 'react-router-dom';

import { useAuth } from './auth';
import {
  createConversationNote,
  fetchConversationDetail,
  fetchConversationNotes,
  handoffConversation,
  pauseConversationAi,
  resumeConversationAi,
  type ConversationDetail,
  type ConversationDetailMessage,
  type ConversationErrorItem,
  type ConversationHandoffActionResponse,
  type ConversationNote,
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

type HandoffAction = 'handoff' | 'pause-ai' | 'resume-ai';

function getHandoffStatusDescription(status: string): string {
  switch (status) {
    case 'ai_active':
      return 'AI is active and can continue sending automatic replies.';
    case 'human_pending':
      return 'The system is waiting for an operator to confirm human takeover.';
    case 'human_active':
      return 'A human operator has taken over this conversation and AI should stay silent.';
    case 'ai_paused':
      return 'AI replies are paused until an operator resumes automation.';
    case 'closed':
      return 'Closed conversations cannot change handoff state.';
    default:
      return 'This conversation has an unknown handoff state.';
  }
}

function getHandoffPillClass(status: string): string {
  switch (status) {
    case 'ai_active':
      return 'status-pill success-pill';
    case 'human_active':
      return 'status-pill warning-pill';
    case 'ai_paused':
      return 'status-pill paused-pill';
    case 'closed':
      return 'status-pill error-pill';
    default:
      return 'status-pill muted-pill';
  }
}

function isActionEnabled(
  action: HandoffAction,
  detail: ConversationDetail,
): boolean {
  if (detail.status === 'closed' || detail.handoff_status === 'closed') {
    return false;
  }

  switch (action) {
    case 'handoff':
      return ['ai_active', 'human_pending'].includes(detail.handoff_status);
    case 'pause-ai':
      return ['ai_active', 'human_active'].includes(detail.handoff_status);
    case 'resume-ai':
      return ['human_active', 'ai_paused'].includes(detail.handoff_status);
    default:
      return false;
  }
}

function getActionLabel(action: HandoffAction, isSubmitting: boolean): string {
  if (!isSubmitting) {
    switch (action) {
      case 'handoff':
        return 'Take over';
      case 'pause-ai':
        return 'Pause AI';
      case 'resume-ai':
        return 'Resume AI';
      default:
        return '';
    }
  }

  switch (action) {
    case 'handoff':
      return 'Taking over...';
    case 'pause-ai':
      return 'Pausing AI...';
    case 'resume-ai':
      return 'Resuming AI...';
    default:
      return '';
  }
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

function NoteItem({ note }: { note: ConversationNote }) {
  return (
    <article className="detail-list-item note-item">
      <div className="detail-list-item-header">
        <h4>Internal operator note</h4>
        <time dateTime={note.created_at}>{formatTimestamp(note.created_at)}</time>
      </div>
      <p className="timeline-item-content">{note.content}</p>
    </article>
  );
}

export function ConversationDetailPage() {
  const { token } = useAuth();
  const { conversationId } = useParams();
  const [detail, setDetail] = useState<ConversationDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [notes, setNotes] = useState<ConversationNote[]>([]);
  const [isNotesLoading, setIsNotesLoading] = useState(true);
  const [notesErrorMessage, setNotesErrorMessage] = useState<string | null>(null);
  const [noteDraft, setNoteDraft] = useState('');
  const [isSubmittingNote, setIsSubmittingNote] = useState(false);
  const [noteSubmitErrorMessage, setNoteSubmitErrorMessage] = useState<string | null>(null);
  const [actionErrorMessage, setActionErrorMessage] = useState<string | null>(null);
  const [activeAction, setActiveAction] = useState<HandoffAction | null>(null);
  const [requestVersion, setRequestVersion] = useState(0);
  const [notesRequestVersion, setNotesRequestVersion] = useState(0);

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
    setActionErrorMessage(null);

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

  useEffect(() => {
    if (!token || !conversationId) {
      setNotes([]);
      setIsNotesLoading(false);
      setNotesErrorMessage('Conversation detail route is missing an id.');
      return;
    }

    let cancelled = false;
    setIsNotesLoading(true);
    setNotesErrorMessage(null);
    setNoteSubmitErrorMessage(null);

    void fetchConversationNotes(token, conversationId)
      .then((response) => {
        if (!cancelled) {
          setNotes(response.items);
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setNotes([]);
          setNotesErrorMessage(
            error instanceof Error ? error.message : 'Unable to load internal notes.',
          );
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsNotesLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [conversationId, notesRequestVersion, token]);

  function handleRetry() {
    setRequestVersion((current) => current + 1);
  }

  function handleNotesRetry() {
    setNotesRequestVersion((current) => current + 1);
  }

  function handleNoteDraftChange(event: ChangeEvent<HTMLTextAreaElement>) {
    setNoteDraft(event.target.value);
  }

  async function handleNoteSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!token || !conversationId) {
      return;
    }

    const trimmedContent = noteDraft.trim();
    if (!trimmedContent) {
      return;
    }

    setIsSubmittingNote(true);
    setNoteSubmitErrorMessage(null);

    try {
      const createdNote = await createConversationNote(token, conversationId, trimmedContent);
      setNotes((current) => [...current, createdNote]);
      setNoteDraft('');
      setNotesErrorMessage(null);
    } catch (error) {
      setNoteSubmitErrorMessage(
        error instanceof Error ? error.message : 'Unable to save internal note.',
      );
    } finally {
      setIsSubmittingNote(false);
    }
  }

  async function handleHandoffAction(action: HandoffAction) {
    if (!token || !conversationId || !detail) {
      return;
    }

    setActiveAction(action);
    setActionErrorMessage(null);

    const requestByAction: Record<
      HandoffAction,
      (accessToken: string, id: string) => Promise<ConversationHandoffActionResponse>
    > = {
      handoff: handoffConversation,
      'pause-ai': pauseConversationAi,
      'resume-ai': resumeConversationAi,
    };

    try {
      const response = await requestByAction[action](token, conversationId);
      setDetail((current) =>
        current
          ? {
              ...current,
              handoff_status: response.handoff_status,
              assigned_agent_id: response.assigned_agent_id,
            }
          : current,
      );
    } catch (error) {
      setActionErrorMessage(
        error instanceof Error ? error.message : 'Unable to update handoff status.',
      );
    } finally {
      setActiveAction(null);
    }
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
  const isMutating = activeAction !== null;
  const handoffActions: HandoffAction[] = ['handoff', 'pause-ai', 'resume-ai'];

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
            <div className="detail-summary-block handoff-controls">
              <div className="handoff-controls-header">
                <div>
                  <h4>Handoff controls</h4>
                  <p className="handoff-status-copy">
                    Use the minimal operator controls for human takeover and AI state changes.
                  </p>
                </div>
                <span className={getHandoffPillClass(detail.handoff_status)}>
                  {formatLabel(detail.handoff_status)}
                </span>
              </div>
              <p className="handoff-status-copy">
                {getHandoffStatusDescription(detail.handoff_status)}
              </p>
              {actionErrorMessage ? (
                <p className="form-error detail-inline-feedback" role="alert">
                  {actionErrorMessage}
                </p>
              ) : null}
              <div className="handoff-actions">
                {handoffActions.map((action) => {
                  const isSubmitting = activeAction === action;
                  return (
                    <button
                      className={action === 'resume-ai' ? 'primary-button' : 'secondary-button'}
                      disabled={!isActionEnabled(action, detail) || isMutating}
                      key={action}
                      onClick={() => {
                        void handleHandoffAction(action);
                      }}
                      type="button"
                    >
                      {getActionLabel(action, isSubmitting)}
                    </button>
                  );
                })}
              </div>
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
            <p className="eyebrow">Internal only</p>
            <h3>Internal notes</h3>
            <p>
              These notes stay inside the operator console and are never shown as
              customer-facing messages.
            </p>
          </div>

          <form className="notes-composer" onSubmit={handleNoteSubmit}>
            <label className="field">
              <span>Add internal note</span>
              <textarea
                disabled={isSubmittingNote}
                name="note-content"
                onChange={handleNoteDraftChange}
                placeholder="Capture follow-up context for operators only."
                rows={4}
                value={noteDraft}
              />
            </label>
            {noteSubmitErrorMessage ? (
              <p className="form-error detail-inline-feedback" role="alert">
                {noteSubmitErrorMessage}
              </p>
            ) : null}
            <div className="notes-composer-actions">
              <button
                className="primary-button"
                disabled={isSubmittingNote || noteDraft.trim().length === 0}
                type="submit"
              >
                {isSubmittingNote ? 'Saving note...' : 'Save internal note'}
              </button>
            </div>
          </form>

          {isNotesLoading ? (
            <section className="loading-panel empty-panel">
              <h4>Loading internal notes...</h4>
              <p>The console is fetching the latest operator-only note history.</p>
            </section>
          ) : notesErrorMessage ? (
            <div className="form-error conversation-feedback" role="alert">
              <div>
                <strong>Internal notes request failed.</strong>
                <p>{notesErrorMessage}</p>
              </div>
              <button className="secondary-button" onClick={handleNotesRetry} type="button">
                Retry
              </button>
            </div>
          ) : notes.length > 0 ? (
            <div className="detail-list-stack">
              {notes.map((note) => (
                <NoteItem key={note.id} note={note} />
              ))}
            </div>
          ) : (
            <section className="loading-panel empty-panel">
              <h4>No internal notes yet</h4>
              <p>Add operator-only context here when follow-up needs to stay internal.</p>
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
