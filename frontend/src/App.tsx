import {
  BrowserRouter,
  Navigate,
  Outlet,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from 'react-router-dom';
import { useState, type FormEvent } from 'react';

import { AuthProvider, useAuth } from './auth';
import { ConversationDetailPage } from './conversation-detail-page';
import { ConversationListPage } from './conversation-list-page';

function ShellLayout() {
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate('/login', { replace: true });
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Phase 2 admin console</p>
          <h1>HiFleetAI Console</h1>
          <p className="header-copy">
            Signed in as <strong>{user?.display_name}</strong> ({user?.role})
          </p>
        </div>
        <button className="secondary-button" onClick={handleLogout} type="button">
          Logout
        </button>
      </header>
      <div className="shell-body">
        <main className="shell-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

function SessionGate() {
  return (
    <section className="panel centered-panel">
      <div className="panel-header">
        <p className="eyebrow">Checking session</p>
        <h2>Loading authentication state</h2>
        <p>The console is verifying whether a saved access token is still valid.</p>
      </div>
    </section>
  );
}

function ProtectedRoute() {
  const { isInitializing, user } = useAuth();
  const location = useLocation();

  if (isInitializing) {
    return <SessionGate />;
  }

  if (!user) {
    return (
      <Navigate
        to="/login"
        replace
        state={{ from: `${location.pathname}${location.search}${location.hash}` }}
      />
    );
  }

  return <Outlet />;
}

function LoginPage() {
  const { isInitializing, isLoggingIn, login, user } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const navigate = useNavigate();
  const location = useLocation();
  const destination =
    typeof location.state?.from === 'string' ? location.state.from : '/';

  if (!isInitializing && user) {
    return <Navigate to={destination} replace />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);

    try {
      await login({ username, password });
      navigate(destination, { replace: true });
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : 'Login request failed',
      );
    }
  }

  return (
    <div className="login-page">
      <section className="panel login-panel">
        <div className="panel-header">
          <p className="eyebrow">Console access</p>
          <h1>Login to HiFleetAI Console</h1>
          <p>
            Use the local admin credentials exposed by the backend auth
            foundation to enter the protected console shell.
          </p>
        </div>
        <form className="login-form" onSubmit={handleSubmit}>
          <label className="field">
            <span>Username</span>
            <input
              autoComplete="username"
              name="username"
              onChange={(event) => setUsername(event.target.value)}
              required
              type="text"
              value={username}
            />
          </label>
          <label className="field">
            <span>Password</span>
            <input
              autoComplete="current-password"
              name="password"
              onChange={(event) => setPassword(event.target.value)}
              required
              type="password"
              value={password}
            />
          </label>
          {errorMessage ? (
            <p className="form-error" role="alert">
              {errorMessage}
            </p>
          ) : null}
          <button className="primary-button" disabled={isLoggingIn} type="submit">
            {isLoggingIn ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
      </section>
    </div>
  );
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<ShellLayout />}>
          <Route path="/" element={<ConversationListPage />} />
          <Route
            path="/conversations/:conversationId"
            element={<ConversationDetailPage />}
          />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
