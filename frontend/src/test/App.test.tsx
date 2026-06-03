// @vitest-environment jsdom

import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';

import { AppRoutes } from '../App';
import { AUTH_TOKEN_STORAGE_KEY, AuthProvider } from '../auth';

describe('App auth routing', () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    localStorage.clear();
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
    const fetchMock = vi.fn(async () =>
      new Response(
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
      ),
    );
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

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/auth/me',
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer saved-access-token',
        }),
      }),
    );
    expect(container.textContent).toContain('HiFleetAI Console');
    expect(container.textContent).toContain('Logout');
  });
});
