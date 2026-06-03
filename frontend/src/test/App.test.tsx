import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';

import { AppRoutes } from '../App';

describe('App bootstrap shell', () => {
  it('renders the shell heading and primary navigation', () => {
    const html = renderToStaticMarkup(
      <MemoryRouter initialEntries={['/']}>
        <AppRoutes />
      </MemoryRouter>,
    );

    expect(html).toContain('HiFleetAI Console');
    expect(html).toContain('Overview');
    expect(html).toContain('Workbench');
    expect(html).toContain('System');
    expect(html).toContain('neutral admin shell');
  });
});
