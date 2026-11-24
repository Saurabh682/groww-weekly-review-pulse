import React from 'react';
import { render } from '@testing-library/react';
import { MemoryRouter, useLocation, useRoutes } from 'react-router-dom';
import { routes } from '../src/app/router';

const Pages: React.FC<{ onPath: (path: string) => void }> = ({ onPath }) => {
  onPath(useLocation().pathname);
  return useRoutes(routes);
};

export function openRoute(route: string) {
  let path = route;
  const view = render(
    <MemoryRouter initialEntries={[route]}>
      <Pages onPath={(next) => { path = next; }} />
    </MemoryRouter>,
  );
  return { ...view, currentPath: () => path };
}
