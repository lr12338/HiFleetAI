export type AuthUser = {
  username: string;
  display_name: string;
  role: string;
  status: string;
};

export type LoginRequest = {
  username: string;
  password: string;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUser;
};

const API_PREFIX = '/api/v1/auth';

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

async function requestJson<T>(
  path: string,
  init: RequestInit,
): Promise<T> {
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

export function loginWithPassword(
  payload: LoginRequest,
): Promise<LoginResponse> {
  return requestJson<LoginResponse>(`${API_PREFIX}/login`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function fetchCurrentUser(accessToken: string): Promise<AuthUser> {
  return requestJson<AuthUser>(`${API_PREFIX}/me`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}
