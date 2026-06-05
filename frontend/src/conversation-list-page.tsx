import { useEffect, useState, type ChangeEvent, type FormEvent } from 'react';
import { Link } from 'react-router-dom';

import { useAuth } from './auth';
import {
  fetchConversationList,
  type ConversationFilters,
  type ConversationListItem,
} from './conversations-client';

const INITIAL_FILTERS: ConversationFilters = {
  status: '',
  channel: '',
  keyword: '',
};

const STATUS_OPTIONS = [
  { value: '', label: 'All statuses' },
  { value: 'open', label: 'Open' },
  { value: 'closed', label: 'Closed' },
];

const CHANNEL_OPTIONS = [
  { value: '', label: 'All channels' },
  { value: 'console', label: 'Console' },
  { value: 'chatwoot', label: 'Chatwoot' },
  { value: 'wechat_official', label: 'WeChat Official' },
  { value: 'wechat_kf', label: 'WeChat Customer Service' },
];

function formatTimestamp(value: string | null): string {
  if (!value) {
    return 'No messages yet';
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

function ConversationCard({ item }: { item: ConversationListItem }) {
  return (
    <article className="conversation-card">
      <div className="conversation-card-header">
        <div>
          <h3>{item.title ?? 'Untitled conversation'}</h3>
          <p className="conversation-summary">
            {item.summary ?? 'No summary has been generated for this conversation yet.'}
          </p>
        </div>
        <div className="conversation-meta-group">
          <span className="status-pill">{formatLabel(item.status)}</span>
          <span className="status-pill muted-pill">
            {formatLabel(item.handoff_status)}
          </span>
        </div>
      </div>
      <dl className="conversation-meta-list">
        <div>
          <dt>Channel</dt>
          <dd>{formatLabel(item.channel_type)}</dd>
        </div>
        <div>
          <dt>Last activity</dt>
          <dd>{formatTimestamp(item.last_message_at)}</dd>
        </div>
        <div>
          <dt>Conversation ID</dt>
          <dd className="conversation-id">{item.id}</dd>
        </div>
      </dl>
      <div className="conversation-card-footer">
        <Link className="secondary-button" to={`/conversations/${item.id}`}>
          Open detail
        </Link>
      </div>
    </article>
  );
}

export function ConversationListPage() {
  const { token } = useAuth();
  const [draftFilters, setDraftFilters] = useState<ConversationFilters>(INITIAL_FILTERS);
  const [appliedFilters, setAppliedFilters] =
    useState<ConversationFilters>(INITIAL_FILTERS);
  const [items, setItems] = useState<ConversationListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [requestVersion, setRequestVersion] = useState(0);

  useEffect(() => {
    if (!token) {
      return;
    }

    let cancelled = false;
    setIsLoading(true);
    setErrorMessage(null);

    void fetchConversationList(token, appliedFilters)
      .then((response) => {
        if (cancelled) {
          return;
        }

        setItems(response.items);
        setTotal(response.total);
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }

        setItems([]);
        setTotal(0);
        setErrorMessage(
          error instanceof Error
            ? error.message
            : 'Unable to load conversations.',
        );
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [appliedFilters, requestVersion, token]);

  function handleFilterChange(
    event: ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) {
    const { name, value } = event.target;
    setDraftFilters((current) => ({
      ...current,
      [name]: value,
    }));
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAppliedFilters({
      status: draftFilters.status.trim(),
      channel: draftFilters.channel.trim(),
      keyword: draftFilters.keyword.trim(),
    });
  }

  function handleReset() {
    setDraftFilters(INITIAL_FILTERS);
    setAppliedFilters(INITIAL_FILTERS);
  }

  function handleRetry() {
    setRequestVersion((current) => current + 1);
  }

  return (
    <section className="panel">
      <div className="panel-header conversation-panel-header">
        <div>
          <p className="eyebrow">Conversation workspace</p>
          <h2>Conversations</h2>
          <p>
            Review the latest protected conversations and narrow the list with
            minimal status, channel, and keyword filters.
          </p>
        </div>
        <div className="conversation-total">
          <span>Total</span>
          <strong>{total}</strong>
        </div>
      </div>

      <form className="filter-form" onSubmit={handleSubmit}>
        <label className="field">
          <span>Status</span>
          <select
            name="status"
            onChange={handleFilterChange}
            value={draftFilters.status}
          >
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value || 'all-statuses'} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Channel</span>
          <select
            name="channel"
            onChange={handleFilterChange}
            value={draftFilters.channel}
          >
            {CHANNEL_OPTIONS.map((option) => (
              <option key={option.value || 'all-channels'} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label className="field filter-keyword-field">
          <span>Keyword</span>
          <input
            name="keyword"
            onChange={handleFilterChange}
            placeholder="Search title or summary"
            type="text"
            value={draftFilters.keyword}
          />
        </label>

        <div className="filter-actions">
          <button className="primary-button" type="submit">
            Apply filters
          </button>
          <button
            className="secondary-button"
            onClick={handleReset}
            type="button"
          >
            Reset
          </button>
        </div>
      </form>

      {errorMessage ? (
        <div className="form-error conversation-feedback" role="alert">
          <div>
            <strong>Unable to load conversations.</strong>
            <p>{errorMessage}</p>
          </div>
          <button className="secondary-button" onClick={handleRetry} type="button">
            Retry
          </button>
        </div>
      ) : null}

      {isLoading ? (
        <section className="conversation-feedback loading-panel" aria-live="polite">
          <p className="eyebrow">Loading</p>
          <h3>Loading conversations...</h3>
          <p>The console is fetching the latest protected conversation list.</p>
        </section>
      ) : null}

      {!isLoading && !errorMessage && total === 0 ? (
        <section className="conversation-feedback empty-panel">
          <p className="eyebrow">No results</p>
          <h3>No conversations found</h3>
          <p>Try changing the filters or clearing the keyword search.</p>
        </section>
      ) : null}

      {!errorMessage && total > 0 ? (
        <div className="conversation-list" aria-live="polite">
          {items.map((item) => (
            <ConversationCard item={item} key={item.id} />
          ))}
        </div>
      ) : null}
    </section>
  );
}
