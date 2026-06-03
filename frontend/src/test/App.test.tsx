// @vitest-environment jsdom

import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';

import { AppRoutes } from '../App';
import { AUTH_TOKEN_STORAGE_KEY, AuthProvider } from '../auth';

type ReactActEnvironmentGlobal = typeof globalThis & {
  IS_REACT_ACT_ENVIRONMENT?: boolean;
};

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
      await Promise.resolve();
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
      await Promise.resolve();
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
      await Promise.resolve();
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
});
