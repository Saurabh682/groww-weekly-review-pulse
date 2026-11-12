import { createBrowserRouter, Navigate } from 'react-router-dom';
import { Shell } from './Shell';
import { WeeklyPulsePage } from '../features/pulse/WeeklyPulsePage';
import { ThemesPage } from '../features/themes/ThemesPage';
import { RunPublishPage } from '../features/run/RunPublishPage';
import { DataImportPage } from '../features/import/DataImportPage';
import { HelpPage } from '../features/help/HelpPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Shell />,
    children: [
      {
        index: true,
        element: <WeeklyPulsePage />,
      },
      {
        path: 'themes',
        element: <ThemesPage />,
      },
      {
        path: 'run',
        element: <RunPublishPage />,
      },
      {
        path: 'import',
        element: <DataImportPage />,
      },
      {
        path: 'help',
        element: <HelpPage />,
      },
      {
        path: '*',
        element: <Navigate to="/" replace />,
      },
    ],
  },
]);
