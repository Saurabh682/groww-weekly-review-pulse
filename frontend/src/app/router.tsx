import { createBrowserRouter, Navigate, RouteObject } from 'react-router-dom';
import { Shell } from './Shell';
import { AppOverviewPage } from '../features/app-overview/AppOverviewPage';
import { AppWeekPage } from '../features/app-overview/AppWeekPage';
import { FirstAppRedirect } from '../features/app-overview/FirstAppRedirect';
import { WeeklyPulsePage } from '../features/pulse/WeeklyPulsePage';
import { ThemesPage } from '../features/themes/ThemesPage';
import { RunPublishPage } from '../features/run/RunPublishPage';
import { DataImportPage } from '../features/import/DataImportPage';
import { ManageAppsPage } from '../features/manage-apps/ManageAppsPage';
import { HelpPage } from '../features/help/HelpPage';

export const routes: RouteObject[] = [
  {
    path: '/',
    element: <Shell />,
    children: [
      { index: true, element: <FirstAppRedirect /> },
      { path: 'apps/:appKey', element: <AppOverviewPage /> },
      { path: 'apps/:appKey/weeks/:week', element: <AppWeekPage /> },
      { path: 'manage', element: <ManageAppsPage /> },
      { path: 'sample', element: <WeeklyPulsePage /> },
      { path: 'themes', element: <ThemesPage /> },
      { path: 'run', element: <RunPublishPage /> },
      { path: 'import', element: <DataImportPage /> },
      { path: 'help', element: <HelpPage /> },
      { path: '*', element: <Navigate to="/" replace /> },
    ],
  },
];

export const createRouter = () => createBrowserRouter(routes);
