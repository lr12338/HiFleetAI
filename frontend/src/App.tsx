import {
  BrowserRouter,
  NavLink,
  Outlet,
  Route,
  Routes,
} from 'react-router-dom';

type PlaceholderPageProps = {
  title: string;
  summary: string;
  details: string[];
};

function PlaceholderPage({ title, summary, details }: PlaceholderPageProps) {
  return (
    <section className="panel">
      <div className="panel-header">
        <p className="eyebrow">Bootstrap route</p>
        <h2>{title}</h2>
        <p>{summary}</p>
      </div>
      <ul className="detail-list">
        {details.map((detail) => (
          <li key={detail}>{detail}</li>
        ))}
      </ul>
    </section>
  );
}

function ShellLayout() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Phase 2 admin console</p>
          <h1>HiFleetAI Console</h1>
        </div>
        <p className="header-copy">
          This bootstrap provides a neutral admin shell, shared navigation, and
          buildable routes for later frontend tasks.
        </p>
      </header>
      <div className="shell-body">
        <aside className="shell-nav" aria-label="Primary">
          <NavLink to="/" end>
            Overview
          </NavLink>
          <NavLink to="/workbench">Workbench</NavLink>
          <NavLink to="/system">System</NavLink>
        </aside>
        <main className="shell-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

function NotFoundPage() {
  return (
    <section className="panel">
      <div className="panel-header">
        <p className="eyebrow">Route status</p>
        <h2>Page not found</h2>
        <p>The requested route is outside the bootstrap shell.</p>
      </div>
    </section>
  );
}

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<ShellLayout />}>
        <Route
          path="/"
          element={
            <PlaceholderPage
              title="Overview"
              summary="The root route confirms the app shell mounts successfully and keeps Phase 2 navigation stable."
              details={[
                'Shared layout with header, nav, and content frame',
                'Placeholder copy only, with no business data or auth flow',
                'Ready to host protected routes in later scoped tasks',
              ]}
            />
          }
        />
        <Route
          path="/workbench"
          element={
            <PlaceholderPage
              title="Workbench"
              summary="A neutral secondary route exists so future pages can plug into the shell without changing the bootstrap structure."
              details={[
                'Route wiring is handled with react-router-dom',
                'Layout boundaries are already visible during local dev',
                'No conversation list, detail, or handoff logic is implemented here',
              ]}
            />
          }
        />
        <Route
          path="/system"
          element={
            <PlaceholderPage
              title="System"
              summary="A third placeholder route validates build output for multiple route entries and gives later work a stable navigation target."
              details={[
                'Minimal content keeps this task strictly within bootstrap scope',
                'Future settings or status surfaces can replace this placeholder',
                'The route remains free of backend integration or write actions',
              ]}
            />
          }
        />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}
