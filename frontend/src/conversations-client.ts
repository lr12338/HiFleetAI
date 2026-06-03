export type ConversationListItem = {
  id: string;
  channel_type: string;
  title: string | null;
  status: string;
  handoff_status: string;
  summary: string | null;
  last_message_at: string | null;
  created_at: string;
  updated_at: string;
};

export type ConversationListResponse = {
  items: ConversationListItem[];
  total: number;
};

export type ConversationDetailMessage = {
  id: string;
  sender_type: string;
  sender_id: string | null;
  message_type: string;
  content: string | null;
  content_payload: Record<string, unknown> | null;
  send_status: string;
  created_at: string;
};

export type ConversationToolCallSummary = {
  id: string;
  message_id: string | null;
  tool_name: string;
  status: string;
  latency_ms: number | null;
  error_message: string | null;
  created_at: string;
};

export type ConversationErrorItem = {
  id: string;
  message_id: string | null;
  source: string;
  code: string;
  message: string | null;
  created_at: string;
  tool_name?: string | null;
};

export type ConversationDetail = {
  id: string;
  user_id: string | null;
  channel_type: string;
  title: string | null;
  status: string;
  handoff_status: string;
  assigned_agent_id: string | null;
  summary: string | null;
  metadata: Record<string, unknown> | null;
  last_message_at: string | null;
  created_at: string;
  updated_at: string;
  messages: ConversationDetailMessage[];
  tool_calls: ConversationToolCallSummary[];
  error_context: {
    model_errors: ConversationErrorItem[];
    tool_errors: ConversationErrorItem[];
  };
};

export type ConversationFilters = {
  status: string;
  channel: string;
  keyword: string;
};

const API_PREFIX = '/api/v1/conversations';

type ApiErrorPayload = {
  detail?: string;
};

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

async function requestJson<T>(path: string, init: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...(init.body ? { 'Content-Type': 'application/json' } : {}),
      ...(init.headers ?? {}),
    },
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  return (await response.json()) as T;
}

function buildConversationListPath(filters: ConversationFilters): string {
  const params = new URLSearchParams();

  if (filters.status.trim()) {
    params.set('status', filters.status.trim());
  }

  if (filters.channel.trim()) {
    params.set('channel', filters.channel.trim());
  }

  if (filters.keyword.trim()) {
    params.set('keyword', filters.keyword.trim());
  }

  const query = params.toString();
  return query ? `${API_PREFIX}?${query}` : API_PREFIX;
}

export function fetchConversationList(
  accessToken: string,
  filters: ConversationFilters,
): Promise<ConversationListResponse> {
  return requestJson<ConversationListResponse>(buildConversationListPath(filters), {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export function fetchConversationDetail(
  accessToken: string,
  conversationId: string,
): Promise<ConversationDetail> {
  return requestJson<ConversationDetail>(
    `${API_PREFIX}/${encodeURIComponent(conversationId)}`,
    {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    },
  );
}
