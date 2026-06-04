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

function setTextareaValue(element: HTMLTextAreaElement, value: string) {
  const valueSetter = Object.getOwnPropertyDescriptor(
    HTMLTextAreaElement.prototype,
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

function buildHarnessRunSummary(overrides: Record<string, unknown> = {}) {
  return {
    id: 'run-1',
    source: 'database',
    run_name: 'Regression smoke',
    status: 'failed',
    summary: {
      total: 2,
      passed: 1,
      failed: 1,
      pass_rate: 0.5,
    },
    created_at: '2026-06-03T15:00:00',
    finished_at: '2026-06-03T15:05:00',
    category: 'regression',
    agent_base_url: 'http://localhost:8000',
    ...overrides,
  };
}

function buildHarnessRunDetail(overrides: Record<string, unknown> = {}) {
  return {
    ...buildHarnessRunSummary(),
    model_config: {
      provider: 'ark',
      model: 'deepseek-v4-flash-260425',
    },
    results: [
      {
        id: 'result-1',
        case_id: 'faq_001',
        status: 'passed',
        passed: true,
        score: 1,
        failure_reason: null,
        actual_output: {
          reply: {
            type: 'text',
            content: '正常返回',
          },
        },
        category: 'faq',
        assertions: [{ name: 'answer_present', passed: true, message: 'ok' }],
        agent_result: {
          status: 'success',
          http_status: 200,
        },
        created_at: '2026-06-03T15:00:30',
      },
      {
        id: 'result-2',
        case_id: 'faq_002',
        status: 'failed',
        passed: false,
        score: 0,
        failure_reason: 'Expected refund policy reference.',
        actual_output: {
          reply: {
            type: 'text',
            content: '缺少关键信息',
          },
        },
        category: 'faq',
        assertions: [{ name: 'refund_policy', passed: false, message: 'missing' }],
        agent_result: {
          status: 'failed',
          http_status: 200,
        },
        created_at: '2026-06-03T15:04:00',
      },
    ],
    ...overrides,
  };
}

function buildNotesListResponse(
  overrides: Partial<{
    items: Array<{
      id: string;
      conversation_id: string;
      author_id: string | null;
      content: string;
      created_at: string;
    }>;
    total: number;
  }> = {},
) {
  const items =
    overrides.items ?? [
      {
        id: 'note-1',
        conversation_id: 'conversation-1',
        author_id: 'admin-user-1',
        content: 'First operator note',
        created_at: '2026-06-03T12:01:00Z',
      },
    ];

  return {
    items,
    total: overrides.total ?? items.length,
  };
}

function buildTestChatResponse(overrides: Record<string, unknown> = {}) {
  return {
    conversation_id: 'conversation-chat-1',
    message_id: 'assistant-message-1',
    handoff_status: 'ai_active',
    reply: {
      type: 'text',
      content: '已按 MVP 模式记录技能调用请求，目标关键词为 EVER GIVEN。',
    },
    tool_calls: [
      {
        tool_name: 'ship.position.query',
        status: 'mocked',
        input_payload: { keyword: 'EVER GIVEN' },
        output_payload: { result: 'mocked_skill_execution' },
      },
    ],
    sources: [],
    metadata: {
      persistence_status: 'persisted',
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

      if (url === '/api/v1/conversations/conversation-1/notes') {
        return createJsonResponse(buildNotesListResponse());
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
    expect(container.textContent).toContain('Internal notes');
    expect(container.textContent).toContain('First operator note');
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

      if (url === '/api/v1/conversations/conversation-1/notes') {
        return createJsonResponse(buildNotesListResponse({ items: [], total: 0 }));
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

  it('renders the internal notes block on the detail page', async () => {
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

      if (url === '/api/v1/conversations/conversation-1/notes') {
        return createJsonResponse(buildNotesListResponse({ items: [], total: 0 }));
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

    expect(container.textContent).toContain('Internal notes');
    expect(container.textContent).toContain(
      'These notes stay inside the operator console and are never shown as customer-facing messages.',
    );
    expect(container.textContent).toContain('No internal notes yet');
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/conversations/conversation-1/notes',
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer saved-access-token',
        }),
      }),
    );
  });

  it('renders the internal notes list returned by the API', async () => {
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

      if (url === '/api/v1/conversations/conversation-1/notes') {
        return createJsonResponse(
          buildNotesListResponse({
            items: [
              {
                id: 'note-1',
                conversation_id: 'conversation-1',
                author_id: 'admin-user-1',
                content: 'First operator note',
                created_at: '2026-06-03T12:01:00Z',
              },
              {
                id: 'note-2',
                conversation_id: 'conversation-1',
                author_id: 'admin-user-1',
                content: 'Second operator note',
                created_at: '2026-06-03T12:02:00Z',
              },
            ],
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

    expect(container.textContent).toContain('First operator note');
    expect(container.textContent).toContain('Second operator note');
  });

  it('creates an internal note and updates the UI after success', async () => {
    localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, 'saved-access-token');
    const notes = [
      {
        id: 'note-1',
        conversation_id: 'conversation-1',
        author_id: 'admin-user-1',
        content: 'First operator note',
        created_at: '2026-06-03T12:01:00Z',
      },
    ];

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

      if (url === '/api/v1/conversations/conversation-1') {
        return createJsonResponse(buildConversationDetail());
      }

      if (url === '/api/v1/conversations/conversation-1/notes' && method === 'GET') {
        return createJsonResponse(buildNotesListResponse({ items: notes }));
      }

      if (url === '/api/v1/conversations/conversation-1/notes' && method === 'POST') {
        notes.push({
          id: 'note-2',
          conversation_id: 'conversation-1',
          author_id: 'admin-user-1',
          content: 'Escalate to carrier operations today.',
          created_at: '2026-06-03T12:03:00Z',
        });
        return createJsonResponse(notes[1], 201);
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

    const noteField = container.querySelector(
      'textarea[name="note-content"]',
    ) as HTMLTextAreaElement | null;
    const saveButton = getButtonByText(container, 'Save internal note');

    expect(noteField).not.toBeNull();
    expect(saveButton).not.toBeNull();

    await act(async () => {
      setTextareaValue(noteField!, 'Escalate to carrier operations today.');
    });

    await act(async () => {
      clickButton(saveButton!);
      await flushPromises();
    });

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/conversations/conversation-1/notes',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          Authorization: 'Bearer saved-access-token',
          'Content-Type': 'application/json',
        }),
        body: JSON.stringify({
          content: 'Escalate to carrier operations today.',
        }),
      }),
    );
    expect(container.textContent).toContain('Escalate to carrier operations today.');
    expect((container.querySelector('textarea[name="note-content"]') as HTMLTextAreaElement).value).toBe(
      '',
    );
  });

  it('shows an error when creating an internal note fails', async () => {
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

      if (url === '/api/v1/conversations/conversation-1') {
        return createJsonResponse(buildConversationDetail());
      }

      if (url === '/api/v1/conversations/conversation-1/notes' && method === 'GET') {
        return createJsonResponse(buildNotesListResponse({ items: [], total: 0 }));
      }

      if (url === '/api/v1/conversations/conversation-1/notes' && method === 'POST') {
        return createJsonResponse(
          { detail: 'Internal note content could not be saved.' },
          500,
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

    const noteField = container.querySelector(
      'textarea[name="note-content"]',
    ) as HTMLTextAreaElement | null;

    expect(noteField).not.toBeNull();

    await act(async () => {
      setTextareaValue(noteField!, 'This save should fail.');
    });

    await act(async () => {
      clickButton(getButtonByText(container, 'Save internal note')!);
      await flushPromises();
    });

    expect(container.textContent).toContain('Internal note content could not be saved.');
    expect((container.querySelector('textarea[name="note-content"]') as HTMLTextAreaElement).value).toBe(
      'This save should fail.',
    );
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

      if (url === '/api/v1/conversations/conversation-1/notes' && method === 'GET') {
        return createJsonResponse(buildNotesListResponse({ items: [], total: 0 }));
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

      if (url === '/api/v1/conversations/conversation-1/notes' && method === 'GET') {
        return createJsonResponse(buildNotesListResponse({ items: [], total: 0 }));
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

      if (url === '/api/v1/conversations/conversation-1/notes') {
        return createJsonResponse(buildNotesListResponse({ items: [], total: 0 }));
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

  it('enters the protected Harness page when a saved token is present', async () => {
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

      if (url === '/api/v1/harness/runs') {
        return createJsonResponse({
          total: 1,
          items: [buildHarnessRunSummary()],
        });
      }

      throw new Error(`Unexpected request: ${url}`);
    });
    vi.stubGlobal('fetch', fetchMock);

    await act(async () => {
      root.render(
        <MemoryRouter initialEntries={['/harness']}>
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
      '/api/v1/harness/runs',
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer saved-access-token',
        }),
      }),
    );
    expect(container.textContent).toContain('Harness runs');
    expect(container.textContent).toContain('Regression smoke');
    expect(container.textContent).toContain('Harness Results');
  });

  it('renders Harness run list summary cards', async () => {
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

      if (url === '/api/v1/harness/runs') {
        return createJsonResponse({
          total: 2,
          items: [
            buildHarnessRunSummary(),
            buildHarnessRunSummary({
              id: 'run-2',
              run_name: 'Handoff happy path',
              status: 'passed',
              summary: {
                total: 1,
                passed: 1,
                failed: 0,
                pass_rate: 1,
              },
              category: 'handoff',
            }),
          ],
        });
      }

      throw new Error(`Unexpected request: ${url}`);
    });
    vi.stubGlobal('fetch', fetchMock);

    await act(async () => {
      root.render(
        <MemoryRouter initialEntries={['/harness']}>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </MemoryRouter>,
      );
    });

    await act(async () => {
      await flushPromises();
    });

    expect(container.textContent).toContain('Total runs');
    expect(container.textContent).toContain('Regression smoke');
    expect(container.textContent).toContain('Handoff happy path');
    expect(container.textContent).toContain('Pass rate');
    expect(container.textContent).toContain('50%');
    expect(container.textContent).toContain('100%');
  });

  it('renders Harness run detail with failed case information', async () => {
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

      if (url === '/api/v1/harness/runs') {
        return createJsonResponse({
          total: 1,
          items: [buildHarnessRunSummary()],
        });
      }

      if (url === '/api/v1/harness/runs/run-1') {
        return createJsonResponse(buildHarnessRunDetail());
      }

      throw new Error(`Unexpected request: ${url}`);
    });
    vi.stubGlobal('fetch', fetchMock);

    await act(async () => {
      root.render(
        <MemoryRouter initialEntries={['/harness/run-1']}>
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
      '/api/v1/harness/runs/run-1',
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer saved-access-token',
        }),
      }),
    );
    expect(container.textContent).toContain('Failed cases');
    expect(container.textContent).toContain('faq_002');
    expect(container.textContent).toContain('Expected refund policy reference.');
    expect(container.textContent).toContain('Model configuration');
    expect(container.textContent).toContain('deepseek-v4-flash-260425');
    expect(container.textContent).toContain('All case results');
  });

  it('shows an error when the Harness run list API fails', async () => {
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

      if (url === '/api/v1/harness/runs') {
        return createJsonResponse({ detail: 'Harness backend unavailable' }, 503);
      }

      throw new Error(`Unexpected request: ${url}`);
    });
    vi.stubGlobal('fetch', fetchMock);

    await act(async () => {
      root.render(
        <MemoryRouter initialEntries={['/harness']}>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </MemoryRouter>,
      );
    });

    await act(async () => {
      await flushPromises();
    });

    expect(container.textContent).toContain('Harness run list request failed.');
    expect(container.textContent).toContain('Harness backend unavailable');
    expect(getButtonByText(container, 'Retry')).not.toBeNull();
  });

  it('sends a test chat request and shows the persisted conversation link', async () => {
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

      if (url === '/api/v1/chat' && method === 'POST') {
        return createJsonResponse(buildTestChatResponse());
      }

      throw new Error(`Unexpected request: ${method} ${url}`);
    });
    vi.stubGlobal('fetch', fetchMock);

    await act(async () => {
      root.render(
        <MemoryRouter initialEntries={['/test-chat']}>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </MemoryRouter>,
      );
    });

    await act(async () => {
      await flushPromises();
    });

    const messageField = container.querySelector(
      'textarea[name="message"]',
    ) as HTMLTextAreaElement | null;
    const sendButton = getButtonByText(container, 'Send test message');

    expect(messageField).not.toBeNull();
    expect(sendButton).not.toBeNull();

    await act(async () => {
      setTextareaValue(messageField!, '帮我查一下 EVER GIVEN 当前船位');
      clickButton(sendButton!);
      await flushPromises();
    });

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/chat',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          conversation_id: null,
          channel_type: 'console',
          user: {
            user_id: null,
            display_name: 'Admin User',
          },
          message: {
            type: 'text',
            content: '帮我查一下 EVER GIVEN 当前船位',
            attachments: [],
          },
          metadata: {
            source: 'console_test_chat',
          },
        }),
      }),
    );
    expect(container.textContent).toContain('Test Chat');
    expect(container.textContent).toContain('已按 MVP 模式记录技能调用请求');
    expect(container.textContent).toContain('Persisted');
    expect(container.textContent).toContain('Open persisted conversation');
  });
});
