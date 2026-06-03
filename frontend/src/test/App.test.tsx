// @vitest-environment jsdom

import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';

import { AppRoutes } from '../App';
import { AUTH_TOKEN_STORAGE_KEY, AuthProvider } from '../auth';

type ReactActEnvironmentGlobal = typeof globalThis & {
  IS_REACT_ACT_ENVIRONMENT?: boolean;
};

function createJsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      'Content-Type': 'application/json',
    },
  });
}

function setInputValue(element: HTMLInputElement, value: string) {
  const valueSetter = Object.getOwnPropertyDescriptor(
    HTMLInputElement.prototype,
    'value',
  )?.set;
  valueSetter?.call(element, value);
  element.dispatchEvent(new Event('input', { bubbles: true }));
  element.dispatchEvent(new Event('change', { bubbles: true }));
}

function setSelectValue(element: HTMLSelectElement, value: string) {
  const valueSetter = Object.getOwnPropertyDescriptor(
    HTMLSelectElement.prototype,
    'value',
  )?.set;
  valueSetter?.call(element, value);
  element.dispatchEvent(new Event('change', { bubbles: true }));
}

function clickButton(button: HTMLButtonElement) {
  button.dispatchEvent(
    new MouseEvent('click', {
      bubbles: true,
      cancelable: true,
      button: 0,
    }),
  );
}

async function flushPromises() {
  await Promise.resolve();
  await Promise.resolve();
}

function getButtonByText(
  container: HTMLElement,
  label: string,
): HTMLButtonElement | null {
  return (
    Array.from(container.querySelectorAll('button')).find(
      (button) => button.textContent?.trim() === label,
    ) ?? null
  );
}

function buildConversationDetail(overrides: Record<string, unknown> = {}) {
  return {
    id: 'conversation-1',
    user_id: 'user-1',
    channel_type: 'console',
    title: 'Alpha cargo issue',
    status: 'open',
    handoff_status: 'ai_active',
    assigned_agent_id: null,
    summary: 'Customer asked about cargo visibility.',
    metadata: {
      source: 'pytest-detail',
    },
    last_message_at: '2026-06-03T12:00:00Z',
    created_at: '2026-06-03T11:30:00Z',
    updated_at: '2026-06-03T12:00:00Z',
    messages: [
      {
        id: 'message-1',
        sender_type: 'user',
        sender_id: null,
        message_type: 'text',
        content: 'First user question',
        content_payload: null,
        send_status: 'received',
        created_at: '2026-06-03T11:59:00Z',
      },
      {
        id: 'message-2',
        sender_type: 'assistant',
        sender_id: null,
        message_type: 'text',
        content: 'Assistant answer',
        content_payload: null,
        send_status: 'sent',
        created_at: '2026-06-03T12:00:00Z',
      },
    ],
    tool_calls: [
      {
        id: 'tool-call-1',
        message_id: 'message-1',
        tool_name: 'knowledge.search',
        status: 'success',
        latency_ms: 120,
        error_message: null,
        created_at: '2026-06-03T11:59:30Z',
      },
    ],
    error_context: {
      model_errors: [],
      tool_errors: [],
    },
    ...overrides,
  };
}

describe('App auth routing', () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    localStorage.clear();
    (globalThis as ReactActEnvironmentGlobal).IS_REACT_ACT_ENVIRONMENT = true;
    vi.unstubAllGlobals();
  });

  afterEach(async () => {
    await act(async () => {
      root.unmount();
    });
    container.remove();
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  it('redirects anonymous users to the login page', async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);

    await act(async () => {
      root.render(
        <MemoryRouter initialEntries={['/']}>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </MemoryRouter>,
      );
    });

    expect(container.textContent).toContain('Login to HiFleetAI Console');
    expect(container.textContent).toContain('Username');
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('restores a saved token and enters the protected shell', async () => {
    localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, 'saved-access-token');
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = input.toString();

      if (url === '/api/v1/auth/me') {
        return new Response(
          JSON.stringify({
            username: 'admin_user',
            display_name: 'Admin User',
            role: 'admin',
            status: 'active',
          }),
          {
            status: 200,
            headers: {
              'Content-Type': 'application/json',
            },
          },
        );
      }

      if (url === '/api/v1/conversations') {
        return new Response(
          JSON.stringify({
            total: 1,
            items: [
              {
                id: 'conversation-1',
                channel_type: 'console',
                title: 'Alpha cargo issue',
                status: 'open',
                handoff_status: 'ai_active',
                summary: 'Customer asked about cargo visibility.',
                last_message_at: '2026-06-03T12:00:00Z',
                created_at: '2026-06-03T11:30:00Z',
                updated_at: '2026-06-03T12:00:00Z',
              },
            ],
          }),
          {
            status: 200,
            headers: {
              'Content-Type': 'application/json',
            },
          },
        );
      }

      throw new Error(`Unexpected request: ${url}`);
    });
    vi.stubGlobal('fetch', fetchMock);

    await act(async () => {
      root.render(
        <MemoryRouter initialEntries={['/']}>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </MemoryRouter>,
      );
    });

    await act(async () => {
      await flushPromises();
    });

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/auth/me',
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer saved-access-token',
        }),
      }),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/conversations',
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer saved-access-token',
        }),
      }),
    );
    expect(container.textContent).toContain('Conversations');
    expect(container.textContent).toContain('Alpha cargo issue');
    expect(container.textContent).toContain('Customer asked about cargo visibility.');
  });

  it('submits filters and requests the filtered conversation list', async () => {
    localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, 'saved-access-token');
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = input.toString();

      if (url === '/api/v1/auth/me') {
        return new Response(
          JSON.stringify({
            username: 'admin_user',
            display_name: 'Admin User',
            role: 'admin',
            status: 'active',
          }),
          {
            status: 200,
            headers: {
              'Content-Type': 'application/json',
            },
          },
        );
      }

      if (url === '/api/v1/conversations') {
        return new Response(
          JSON.stringify({
            total: 1,
            items: [
              {
                id: 'conversation-1',
                channel_type: 'console',
                title: 'Alpha cargo issue',
                status: 'open',
                handoff_status: 'ai_active',
                summary: 'Customer asked about cargo visibility.',
                last_message_at: '2026-06-03T12:00:00Z',
                created_at: '2026-06-03T11:30:00Z',
                updated_at: '2026-06-03T12:00:00Z',
              },
            ],
          }),
          {
            status: 200,
            headers: {
              'Content-Type': 'application/json',
            },
          },
        );
      }

      if (
        url ===
        '/api/v1/conversations?status=closed&channel=chatwoot&keyword=billing'
      ) {
        return new Response(
          JSON.stringify({
            total: 1,
            items: [
              {
                id: 'conversation-2',
                channel_type: 'chatwoot',
                title: 'Bravo handoff request',
                status: 'closed',
                handoff_status: 'human_active',
                summary: 'Needs human handoff for billing.',
                last_message_at: '2026-06-03T12:05:00Z',
                created_at: '2026-06-03T11:40:00Z',
                updated_at: '2026-06-03T12:05:00Z',
              },
            ],
          }),
          {
            status: 200,
            headers: {
              'Content-Type': 'application/json',
            },
          },
        );
      }

      throw new Error(`Unexpected request: ${url}`);
    });
    vi.stubGlobal('fetch', fetchMock);

    await act(async () => {
      root.render(
        <MemoryRouter initialEntries={['/']}>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </MemoryRouter>,
      );
    });

    await act(async () => {
      await flushPromises();
    });

    const statusField = container.querySelector(
      'select[name="status"]',
    ) as HTMLSelectElement | null;
    const channelField = container.querySelector(
      'select[name="channel"]',
    ) as HTMLSelectElement | null;
    const keywordField = container.querySelector(
      'input[name="keyword"]',
    ) as HTMLInputElement | null;
    const filterForm = container.querySelector('form');

    expect(statusField).not.toBeNull();
    expect(channelField).not.toBeNull();
    expect(keywordField).not.toBeNull();
    expect(filterForm).not.toBeNull();

    await act(async () => {
      setSelectValue(statusField!, 'closed');
      setSelectValue(channelField!, 'chatwoot');
      setInputValue(keywordField!, 'billing');
      filterForm!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    });

    await act(async () => {
      await flushPromises();
    });

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/conversations?status=closed&channel=chatwoot&keyword=billing',
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer saved-access-token',
        }),
      }),
    );
    expect(container.textContent).toContain('Bravo handoff request');
    expect(container.textContent).toContain('Needs human handoff for billing.');
  });

  it('navigates from the list into the conversation detail page', async () => {
    localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, 'saved-access-token');
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = input.toString();

      if (url === '/api/v1/auth/me') {
        return createJsonResponse({
          username: 'admin_user',
          display_name: 'Admin User',
          role: 'admin',
          status: 'active',
        });
      }

      if (url === '/api/v1/conversations') {
        return createJsonResponse({
          total: 1,
          items: [
            {
              id: 'conversation-1',
              channel_type: 'console',
              title: 'Alpha cargo issue',
              status: 'open',
              handoff_status: 'ai_active',
              summary: 'Customer asked about cargo visibility.',
              last_message_at: '2026-06-03T12:00:00Z',
              created_at: '2026-06-03T11:30:00Z',
              updated_at: '2026-06-03T12:00:00Z',
            },
          ],
        });
      }

      if (url === '/api/v1/conversations/conversation-1') {
        return createJsonResponse(
          buildConversationDetail({
            error_context: {
              model_errors: [
                {
                  id: 'model-error-1',
                  message_id: 'message-2',
                  source: 'model_gateway',
                  code: 'failed',
                  message: 'Synthetic model failure',
                  created_at: '2026-06-03T12:00:10Z',
                },
              ],
              tool_errors: [],
            },
          }),
        );
      }

      throw new Error(`Unexpected request: ${url}`);
    });
    vi.stubGlobal('fetch', fetchMock);

    await act(async () => {
      root.render(
        <MemoryRouter initialEntries={['/']}>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </MemoryRouter>,
      );
    });

    await act(async () => {
      await flushPromises();
    });

    const detailLink = container.querySelector(
      'a[href="/conversations/conversation-1"]',
    ) as HTMLAnchorElement | null;

    expect(detailLink).not.toBeNull();

    await act(async () => {
      detailLink!.dispatchEvent(
        new MouseEvent('click', {
          bubbles: true,
          cancelable: true,
          button: 0,
        }),
      );
    });

    await act(async () => {
      await flushPromises();
    });

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/conversations/conversation-1',
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer saved-access-token',
        }),
      }),
    );
    expect(container.textContent).toContain('Message timeline');
    expect(container.textContent).toContain('First user question');
    expect(container.textContent).toContain('knowledge.search');
    expect(container.textContent).toContain('Synthetic model failure');
  });

  it('renders handoff controls with state-based button availability', async () => {
    localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, 'saved-access-token');
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = input.toString();

      if (url === '/api/v1/auth/me') {
        return createJsonResponse({
          username: 'admin_user',
          display_name: 'Admin User',
          role: 'admin',
          status: 'active',
        });
      }

      if (url === '/api/v1/conversations/conversation-1') {
        return createJsonResponse(buildConversationDetail());
      }

      throw new Error(`Unexpected request: ${url}`);
    });
    vi.stubGlobal('fetch', fetchMock);

    await act(async () => {
      root.render(
        <MemoryRouter initialEntries={['/conversations/conversation-1']}>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </MemoryRouter>,
      );
    });

    await act(async () => {
      await flushPromises();
    });

    const takeOverButton = getButtonByText(container, 'Take over');
    const pauseButton = getButtonByText(container, 'Pause AI');
    const resumeButton = getButtonByText(container, 'Resume AI');

    expect(container.textContent).toContain('Handoff controls');
    expect(container.textContent).toContain('AI is active and can continue sending automatic replies.');
    expect(takeOverButton).not.toBeNull();
    expect(pauseButton).not.toBeNull();
    expect(resumeButton).not.toBeNull();
    expect(takeOverButton?.disabled).toBe(false);
    expect(pauseButton?.disabled).toBe(false);
    expect(resumeButton?.disabled).toBe(true);
  });

  it('updates handoff status after successful handoff, pause, and resume actions', async () => {
    localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, 'saved-access-token');
    let handoffStatus = 'ai_active';
    let assignedAgentId: string | null = null;

    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = input.toString();
      const method = init?.method ?? 'GET';

      if (url === '/api/v1/auth/me') {
        return createJsonResponse({
          username: 'admin_user',
          display_name: 'Admin User',
          role: 'admin',
          status: 'active',
        });
      }

      if (url === '/api/v1/conversations/conversation-1' && method === 'GET') {
        return createJsonResponse(
          buildConversationDetail({
            handoff_status: handoffStatus,
            assigned_agent_id: assignedAgentId,
          }),
        );
      }

      if (url === '/api/v1/conversations/conversation-1/handoff' && method === 'POST') {
        handoffStatus = 'human_active';
        assignedAgentId = 'agent-1';
        return createJsonResponse({
          conversation_id: 'conversation-1',
          handoff_status: handoffStatus,
          assigned_agent_id: assignedAgentId,
          event_type: 'takeover',
        });
      }

      if (url === '/api/v1/conversations/conversation-1/pause-ai' && method === 'POST') {
        handoffStatus = 'ai_paused';
        return createJsonResponse({
          conversation_id: 'conversation-1',
          handoff_status: handoffStatus,
          assigned_agent_id: assignedAgentId,
          event_type: 'pause_ai',
        });
      }

      if (url === '/api/v1/conversations/conversation-1/resume-ai' && method === 'POST') {
        handoffStatus = 'ai_active';
        assignedAgentId = null;
        return createJsonResponse({
          conversation_id: 'conversation-1',
          handoff_status: handoffStatus,
          assigned_agent_id: assignedAgentId,
          event_type: 'resume_ai',
        });
      }

      throw new Error(`Unexpected request: ${method} ${url}`);
    });
    vi.stubGlobal('fetch', fetchMock);

    await act(async () => {
      root.render(
        <MemoryRouter initialEntries={['/conversations/conversation-1']}>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </MemoryRouter>,
      );
    });

    await act(async () => {
      await flushPromises();
    });

    await act(async () => {
      clickButton(getButtonByText(container, 'Take over')!);
      await flushPromises();
    });

    expect(container.textContent).toContain(
      'A human operator has taken over this conversation and AI should stay silent.',
    );
    expect(getButtonByText(container, 'Take over')?.disabled).toBe(true);
    expect(getButtonByText(container, 'Pause AI')?.disabled).toBe(false);
    expect(getButtonByText(container, 'Resume AI')?.disabled).toBe(false);

    await act(async () => {
      clickButton(getButtonByText(container, 'Pause AI')!);
      await flushPromises();
    });

    expect(container.textContent).toContain(
      'AI replies are paused until an operator resumes automation.',
    );
    expect(getButtonByText(container, 'Take over')?.disabled).toBe(true);
    expect(getButtonByText(container, 'Pause AI')?.disabled).toBe(true);
    expect(getButtonByText(container, 'Resume AI')?.disabled).toBe(false);

    await act(async () => {
      clickButton(getButtonByText(container, 'Resume AI')!);
      await flushPromises();
    });

    expect(container.textContent).toContain(
      'AI is active and can continue sending automatic replies.',
    );
    expect(getButtonByText(container, 'Take over')?.disabled).toBe(false);
    expect(getButtonByText(container, 'Pause AI')?.disabled).toBe(false);
    expect(getButtonByText(container, 'Resume AI')?.disabled).toBe(true);
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/conversations/conversation-1/handoff',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          Authorization: 'Bearer saved-access-token',
        }),
      }),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/conversations/conversation-1/pause-ai',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          Authorization: 'Bearer saved-access-token',
        }),
      }),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/conversations/conversation-1/resume-ai',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          Authorization: 'Bearer saved-access-token',
        }),
      }),
    );
  });

  it('shows an error when a handoff action fails', async () => {
    localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, 'saved-access-token');
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = input.toString();
      const method = init?.method ?? 'GET';

      if (url === '/api/v1/auth/me') {
        return createJsonResponse({
          username: 'admin_user',
          display_name: 'Admin User',
          role: 'admin',
          status: 'active',
        });
      }

      if (url === '/api/v1/conversations/conversation-1' && method === 'GET') {
        return createJsonResponse(buildConversationDetail());
      }

      if (url === '/api/v1/conversations/conversation-1/pause-ai' && method === 'POST') {
        return createJsonResponse(
          { detail: "Cannot transition conversation from 'ai_active' to 'ai_paused'." },
          409,
        );
      }

      throw new Error(`Unexpected request: ${method} ${url}`);
    });
    vi.stubGlobal('fetch', fetchMock);

    await act(async () => {
      root.render(
        <MemoryRouter initialEntries={['/conversations/conversation-1']}>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </MemoryRouter>,
      );
    });

    await act(async () => {
      await flushPromises();
    });

    await act(async () => {
      clickButton(getButtonByText(container, 'Pause AI')!);
      await flushPromises();
    });

    expect(container.textContent).toContain(
      "Cannot transition conversation from 'ai_active' to 'ai_paused'.",
    );
    expect(container.textContent).toContain(
      'AI is active and can continue sending automatic replies.',
    );
    expect(getButtonByText(container, 'Pause AI')?.disabled).toBe(false);
  });

  it('disables unavailable handoff actions for paused conversations', async () => {
    localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, 'saved-access-token');
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = input.toString();

      if (url === '/api/v1/auth/me') {
        return createJsonResponse({
          username: 'admin_user',
          display_name: 'Admin User',
          role: 'admin',
          status: 'active',
        });
      }

      if (url === '/api/v1/conversations/conversation-1') {
        return createJsonResponse(
          buildConversationDetail({
            handoff_status: 'ai_paused',
            assigned_agent_id: 'agent-1',
          }),
        );
      }

      throw new Error(`Unexpected request: ${url}`);
    });
    vi.stubGlobal('fetch', fetchMock);

    await act(async () => {
      root.render(
        <MemoryRouter initialEntries={['/conversations/conversation-1']}>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </MemoryRouter>,
      );
    });

    await act(async () => {
      await flushPromises();
    });

    expect(container.textContent).toContain(
      'AI replies are paused until an operator resumes automation.',
    );
    expect(getButtonByText(container, 'Take over')?.disabled).toBe(true);
    expect(getButtonByText(container, 'Pause AI')?.disabled).toBe(true);
    expect(getButtonByText(container, 'Resume AI')?.disabled).toBe(false);
  });
});
