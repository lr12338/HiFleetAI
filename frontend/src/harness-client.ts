type ApiErrorPayload = {
  detail?: string;
};

export type HarnessRunSummary = {
  id: string;
  source: string;
  run_name: string | null;
  status: string;
  summary: Record<string, unknown> | null;
  created_at: string;
  finished_at: string | null;
  category: string | null;
  agent_base_url: string | null;
};

export type HarnessRunListResponse = {
  items: HarnessRunSummary[];
  total: number;
};

export type HarnessRunResult = {
  id: string | null;
  case_id: string | null;
  status: string | null;
  passed: boolean | null;
  score: number | null;
  failure_reason: string | null;
  actual_output: Record<string, unknown> | null;
  category: string | null;
  assertions: Record<string, unknown>[] | null;
  agent_result: Record<string, unknown> | null;
  created_at: string | null;
};

export type HarnessRunDetail = HarnessRunSummary & {
  model_config: Record<string, unknown> | null;
  results: HarnessRunResult[];
};

const API_PREFIX = '/api/v1/harness/runs';

async function parseErrorMessage(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as ApiErrorPayload;
    if (typeof payload.detail === 'string' && payload.detail.length > 0) {
      return payload.detail;
    }
  } catch {
    // Ignore JSON parsing failures and fall through to a generic message.
  }

  return `Request failed with status ${response.status}`;
}

async function requestJson<T>(path: string, accessToken: string): Promise<T> {
  const response = await fetch(path, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  return (await response.json()) as T;
}

export function fetchHarnessRunList(
  accessToken: string,
): Promise<HarnessRunListResponse> {
  return requestJson<HarnessRunListResponse>(API_PREFIX, accessToken);
}

export function fetchHarnessRunDetail(
  accessToken: string,
  runId: string,
): Promise<HarnessRunDetail> {
  return requestJson<HarnessRunDetail>(
    `${API_PREFIX}/${encodeURIComponent(runId)}`,
    accessToken,
  );
}
