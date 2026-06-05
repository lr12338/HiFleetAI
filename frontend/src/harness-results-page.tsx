import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { useAuth } from './auth';
import {
  fetchHarnessRunDetail,
  fetchHarnessRunList,
  type HarnessRunDetail,
  type HarnessRunResult,
  type HarnessRunSummary,
} from './harness-client';

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

function formatLabel(value: string | null): string {
  if (!value) {
    return 'Unknown';
  }

  return value
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function formatJsonBlock(value: Record<string, unknown> | null): string {
  if (!value || Object.keys(value).length === 0) {
    return 'No structured payload recorded.';
  }

  return JSON.stringify(value, null, 2);
}

function getSummaryCount(summary: Record<string, unknown> | null, key: string): string {
  const value = summary?.[key];
  if (typeof value === 'number') {
    return `${value}`;
  }

  return '0';
}

function getPassRate(summary: Record<string, unknown> | null): string {
  const value = summary?.pass_rate;
  if (typeof value === 'number') {
    return `${Math.round(value * 100)}%`;
  }

  return 'Not recorded';
}

function getRunStatusClass(status: string): string {
  switch (status) {
    case 'passed':
      return 'status-pill success-pill';
    case 'failed':
      return 'status-pill error-pill';
    default:
      return 'status-pill muted-pill';
  }
}

function getResultStatusClass(result: HarnessRunResult): string {
  if (result.passed === true || result.status === 'passed') {
    return 'status-pill success-pill';
  }

  if (result.passed === false || result.status === 'failed') {
    return 'status-pill error-pill';
  }

  return 'status-pill muted-pill';
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

function HarnessRunCard({
  item,
  isSelected,
}: {
  item: HarnessRunSummary;
  isSelected: boolean;
}) {
  return (
    <article className={`conversation-card harness-run-card${isSelected ? ' is-selected' : ''}`}>
      <div className="conversation-card-header">
        <div>
          <h3>{item.run_name ?? item.id}</h3>
          <p className="conversation-summary">
            {formatLabel(item.category)} · {formatLabel(item.source)} · Created{' '}
            {formatTimestamp(item.created_at)}
          </p>
        </div>
        <div className="conversation-meta-group">
          <span className={getRunStatusClass(item.status)}>{formatLabel(item.status)}</span>
        </div>
      </div>
      <dl className="conversation-meta-list">
        <div>
          <dt>Total</dt>
          <dd>{getSummaryCount(item.summary, 'total')}</dd>
        </div>
        <div>
          <dt>Failed</dt>
          <dd>{getSummaryCount(item.summary, 'failed')}</dd>
        </div>
        <div>
          <dt>Pass rate</dt>
          <dd>{getPassRate(item.summary)}</dd>
        </div>
      </dl>
      <div className="conversation-card-footer">
        <Link className="secondary-button" to={`/harness/${item.id}`}>
          View run
        </Link>
      </div>
    </article>
  );
}

function FailedResultItem({ result }: { result: HarnessRunResult }) {
  return (
    <article className="detail-list-item error-item">
      <div className="detail-list-item-header">
        <h4>{result.case_id ?? result.id ?? 'Unknown case'}</h4>
        <span className={getResultStatusClass(result)}>
          {formatLabel(result.status ?? (result.passed === false ? 'failed' : 'unknown'))}
        </span>
      </div>
      <p className="timeline-item-content">
        {result.failure_reason ?? 'No explicit failure reason was recorded.'}
      </p>
      <dl className="detail-inline-list">
        <div>
          <dt>Score</dt>
          <dd>{result.score === null ? 'Not recorded' : `${result.score}`}</dd>
        </div>
        <div>
          <dt>Category</dt>
          <dd>{formatLabel(result.category)}</dd>
        </div>
        <div>
          <dt>Created</dt>
          <dd>{formatTimestamp(result.created_at)}</dd>
        </div>
      </dl>
    </article>
  );
}

function HarnessResultItem({ result }: { result: HarnessRunResult }) {
  return (
    <article className="detail-list-item">
      <div className="detail-list-item-header">
        <h4>{result.case_id ?? result.id ?? 'Unknown case'}</h4>
        <span className={getResultStatusClass(result)}>
          {formatLabel(result.status ?? (result.passed === true ? 'passed' : 'unknown'))}
        </span>
      </div>
      <dl className="detail-inline-list">
        <div>
          <dt>Passed</dt>
          <dd>{result.passed === null ? 'Unknown' : result.passed ? 'Yes' : 'No'}</dd>
        </div>
        <div>
          <dt>Score</dt>
          <dd>{result.score === null ? 'Not recorded' : `${result.score}`}</dd>
        </div>
        <div>
          <dt>Created</dt>
          <dd>{formatTimestamp(result.created_at)}</dd>
        </div>
      </dl>
      {result.failure_reason ? (
        <p className="detail-inline-error">{result.failure_reason}</p>
      ) : null}
      <div className="harness-result-payloads">
        <div className="detail-summary-block">
          <h4>Actual output</h4>
          <pre className="json-block">{formatJsonBlock(result.actual_output)}</pre>
        </div>
        <div className="detail-summary-block">
          <h4>Agent result</h4>
          <pre className="json-block">{formatJsonBlock(result.agent_result)}</pre>
        </div>
      </div>
    </article>
  );
}

export function HarnessResultsPage() {
  const { token } = useAuth();
  const { runId } = useParams();
  const [runs, setRuns] = useState<HarnessRunSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [isListLoading, setIsListLoading] = useState(true);
  const [listErrorMessage, setListErrorMessage] = useState<string | null>(null);
  const [listRequestVersion, setListRequestVersion] = useState(0);
  const [detail, setDetail] = useState<HarnessRunDetail | null>(null);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [detailErrorMessage, setDetailErrorMessage] = useState<string | null>(null);
  const [detailRequestVersion, setDetailRequestVersion] = useState(0);

  useEffect(() => {
    if (!token) {
      return;
    }

    let cancelled = false;
    setIsListLoading(true);
    setListErrorMessage(null);

    void fetchHarnessRunList(token)
      .then((response) => {
        if (cancelled) {
          return;
        }

        setRuns(response.items);
        setTotal(response.total);
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }

        setRuns([]);
        setTotal(0);
        setListErrorMessage(
          error instanceof Error ? error.message : 'Unable to load Harness runs.',
        );
      })
      .finally(() => {
        if (!cancelled) {
          setIsListLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [listRequestVersion, token]);

  useEffect(() => {
    if (!token || !runId) {
      setDetail(null);
      setIsDetailLoading(false);
      setDetailErrorMessage(null);
      return;
    }

    let cancelled = false;
    setIsDetailLoading(true);
    setDetailErrorMessage(null);

    void fetchHarnessRunDetail(token, runId)
      .then((response) => {
        if (!cancelled) {
          setDetail(response);
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setDetail(null);
          setDetailErrorMessage(
            error instanceof Error ? error.message : 'Unable to load Harness run detail.',
          );
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsDetailLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [detailRequestVersion, runId, token]);

  const failedResults = useMemo(() => {
    if (!detail) {
      return [];
    }

    return detail.results.filter(
      (result) => result.passed === false || result.status === 'failed',
    );
  }, [detail]);

  function retryList() {
    setListRequestVersion((current) => current + 1);
  }

  function retryDetail() {
    setDetailRequestVersion((current) => current + 1);
  }

  return (
    <section className="detail-page">
      <div className="panel detail-hero">
        <div className="panel-header conversation-panel-header">
          <div>
            <p className="eyebrow">Harness workspace</p>
            <h2>Harness runs</h2>
            <p>
              Review protected Harness execution summaries and open one run to inspect
              failures and raw result payloads.
            </p>
          </div>
          <div className="conversation-total">
            <span>Total runs</span>
            <strong>{total}</strong>
          </div>
        </div>

        {listErrorMessage ? (
          <div className="form-error conversation-feedback" role="alert">
            <div>
              <strong>Harness run list request failed.</strong>
              <p>{listErrorMessage}</p>
            </div>
            <button className="secondary-button" onClick={retryList} type="button">
              Retry
            </button>
          </div>
        ) : null}

        {isListLoading ? (
          <section className="conversation-feedback loading-panel" aria-live="polite">
            <p className="eyebrow">Loading</p>
            <h3>Loading Harness runs...</h3>
            <p>The console is fetching the latest protected Harness result summaries.</p>
          </section>
        ) : null}

        {!isListLoading && !listErrorMessage && total === 0 ? (
          <section className="conversation-feedback empty-panel">
            <p className="eyebrow">No results</p>
            <h3>No Harness runs found</h3>
            <p>The backend has not reported any Harness result summary yet.</p>
          </section>
        ) : null}

        {!listErrorMessage && total > 0 ? (
          <div className="conversation-list" aria-live="polite">
            {runs.map((item) => (
              <HarnessRunCard item={item} isSelected={item.id === runId} key={item.id} />
            ))}
          </div>
        ) : null}
      </div>

      <section className="panel detail-section-panel">
        {isDetailLoading ? (
          <div className="panel-header">
            <p className="eyebrow">Run detail</p>
            <h3>Loading Harness run detail...</h3>
            <p>The selected run is being fetched from the protected API.</p>
          </div>
        ) : detailErrorMessage ? (
          <>
            <div className="panel-header detail-header">
              <div>
                <p className="eyebrow">Run detail</p>
                <h3>Unable to load Harness run</h3>
                <p>The requested run detail could not be rendered.</p>
              </div>
              <button className="secondary-button" onClick={retryDetail} type="button">
                Retry
              </button>
            </div>
            <div className="form-error conversation-feedback" role="alert">
              <div>
                <strong>Harness run detail request failed.</strong>
                <p>{detailErrorMessage}</p>
              </div>
            </div>
          </>
        ) : !runId ? (
          <div className="panel-header">
            <p className="eyebrow">Run detail</p>
            <h3>Select a Harness run</h3>
            <p>Choose one summary card above to inspect failed cases and detailed payloads.</p>
          </div>
        ) : !detail ? (
          <div className="panel-header">
            <p className="eyebrow">Run detail</p>
            <h3>No Harness run detail available</h3>
            <p>The selected run did not return a renderable detail payload.</p>
          </div>
        ) : (
          <div className="detail-content-grid">
            <section className="detail-section">
              <div className="panel-header detail-header">
                <div>
                  <p className="eyebrow">Run detail</p>
                  <h3>{detail.run_name ?? detail.id}</h3>
                  <p>
                    Failed cases are surfaced first so operators can quickly inspect why a
                    run passed or failed.
                  </p>
                </div>
                <div className="detail-header-actions">
                  <span className={getRunStatusClass(detail.status)}>
                    {formatLabel(detail.status)}
                  </span>
                  <Link className="secondary-button" to="/harness">
                    Back to run list
                  </Link>
                </div>
              </div>

              <dl className="detail-meta-grid">
                <DetailMetaItem label="Run ID" value={detail.id} mono />
                <DetailMetaItem label="Source" value={formatLabel(detail.source)} />
                <DetailMetaItem label="Category" value={formatLabel(detail.category)} />
                <DetailMetaItem
                  label="Agent base URL"
                  value={detail.agent_base_url ?? 'Not recorded'}
                  mono
                />
                <DetailMetaItem label="Created" value={formatTimestamp(detail.created_at)} />
                <DetailMetaItem
                  label="Finished"
                  value={formatTimestamp(detail.finished_at)}
                />
              </dl>

              <div className="harness-summary-grid">
                <div className="detail-summary-block">
                  <h4>Total cases</h4>
                  <p>{getSummaryCount(detail.summary, 'total')}</p>
                </div>
                <div className="detail-summary-block">
                  <h4>Failed cases</h4>
                  <p>{getSummaryCount(detail.summary, 'failed')}</p>
                </div>
                <div className="detail-summary-block">
                  <h4>Pass rate</h4>
                  <p>{getPassRate(detail.summary)}</p>
                </div>
              </div>

              <div className="detail-summary-block">
                <h4>Model configuration</h4>
                <pre className="json-block">{formatJsonBlock(detail.model_config)}</pre>
              </div>
            </section>

            <section className="detail-section-panel">
              <div className="panel-header">
                <p className="eyebrow">Failures</p>
                <h3>Failed cases</h3>
                <p>Only failed or explicitly unsuccessful cases are highlighted here.</p>
              </div>
              {failedResults.length > 0 ? (
                <div className="detail-list-stack">
                  {failedResults.map((result) => (
                    <FailedResultItem key={result.id ?? result.case_id ?? 'failed-case'} result={result} />
                  ))}
                </div>
              ) : (
                <section className="loading-panel empty-panel">
                  <h4>No failed cases</h4>
                  <p>The selected run does not contain any recorded failures.</p>
                </section>
              )}
            </section>

            <section className="detail-section-panel">
              <div className="panel-header">
                <p className="eyebrow">Results</p>
                <h3>All case results</h3>
                <p>Raw actual output and agent result payloads are preserved for debugging.</p>
              </div>
              {detail.results.length > 0 ? (
                <div className="detail-list-stack">
                  {detail.results.map((result) => (
                    <HarnessResultItem
                      key={result.id ?? result.case_id ?? 'result-item'}
                      result={result}
                    />
                  ))}
                </div>
              ) : (
                <section className="loading-panel empty-panel">
                  <h4>No results recorded</h4>
                  <p>The backend returned an empty result list for this run.</p>
                </section>
              )}
            </section>
          </div>
        )}
      </section>
    </section>
  );
}
