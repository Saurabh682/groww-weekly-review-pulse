import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { Shell } from '../src/app/Shell';
import { WeeklyPulsePage } from '../src/features/pulse/WeeklyPulsePage';
import { RunPublishPage } from '../src/features/run/RunPublishPage';
import { ThemesPage } from '../src/features/themes/ThemesPage';
import { DataImportPage } from '../src/features/import/DataImportPage';
import { HelpPage } from '../src/features/help/HelpPage';

// Helper to render routes wrapped in Shell
const renderWithRouter = (initialRoute: string) => {
  return render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <Routes>
        <Route path="/" element={<Shell />}>
          <Route index element={<WeeklyPulsePage />} />
          <Route path="themes" element={<ThemesPage />} />
          <Route path="run" element={<RunPublishPage />} />
          <Route path="import" element={<DataImportPage />} />
          <Route path="help" element={<HelpPage />} />
        </Route>
      </Routes>
    </MemoryRouter>
  );
};

describe('Frontend Screens Suite', () => {
  it('WeeklyPulsePage renders score, top 3 themes, verbatim quotes, and action ideas', async () => {
    renderWithRouter('/');

    // Wait for mock API response to resolve and render content
    const themesTitle = await screen.findByText('Top 3 Themes', {}, { timeout: 2000 });
    expect(themesTitle).toBeInTheDocument();

    expect(screen.getByRole('heading', { level: 1, name: 'Weekly Review Pulse' })).toBeInTheDocument();
    expect(screen.getByText('68')).toBeInTheDocument();
    expect(screen.getAllByText('KYC & Onboarding Bottlenecks').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('What Users Said')).toBeInTheDocument();
    expect(screen.getByText('Action Ideas')).toBeInTheDocument();
    expect(screen.getByText('Note checks')).toBeInTheDocument();
  });

  it('RunPublishPage has STRICTLY "View Gmail draft" and NEVER has "Send email"', async () => {
    renderWithRouter('/run');

    const runTitle = await screen.findByText('Run & Publish Pipeline', {}, { timeout: 2000 });
    expect(runTitle).toBeInTheDocument();

    // Check for "View Gmail draft"
    const gmailBtn = screen.getByText('View Gmail draft');
    expect(gmailBtn).toBeInTheDocument();

    // MUST NOT have any "Send email" button
    expect(screen.queryByText(/send email/i)).toBeNull();
    expect(screen.queryByRole('button', { name: /send email/i })).toBeNull();

    // Verify 7-stage stepper track and Invariant matrix exists
    expect(screen.getByText('Pipeline Stage Heartbeat')).toBeInTheDocument();
    expect(screen.getByText('Quality Gate Invariant Verification Matrix')).toBeInTheDocument();
  });

  it('ThemesPage renders themes and 5 of 5 clusters active badge', async () => {
    renderWithRouter('/themes');

    const themesTitle = await screen.findByText('Themes Explorer', {}, { timeout: 2000 });
    expect(themesTitle).toBeInTheDocument();

    expect(screen.getByText('5 of 5 clusters active')).toBeInTheDocument();
    expect(screen.getByText('Cluster Orbit Map')).toBeInTheDocument();
    expect(screen.getByText('Cluster Priority Leaderboard')).toBeInTheDocument();
  });

  it('DataImportPage renders 4 health metrics and dropzone', async () => {
    renderWithRouter('/import');

    const importTitle = await screen.findByText('Data Ingestion & Hygiene', {}, { timeout: 2000 });
    expect(importTitle).toBeInTheDocument();

    expect(screen.getByText('Reviews Cleaned & Indexed')).toBeInTheDocument();
    expect(screen.getByText('Duplicates Pruned')).toBeInTheDocument();
    expect(screen.getByText('Low-Info Excluded')).toBeInTheDocument();
    expect(screen.getByText('PII Entities Redacted')).toBeInTheDocument();
    expect(screen.getByText(/12-Week Ingestion Volume Waveform/i)).toBeInTheDocument();
  });

  it('HelpPage renders app guide, core screens, invariants, and FAQ', async () => {
    renderWithRouter('/help');

    const helpHeading = await screen.findByRole('heading', { level: 1, name: 'App Guide & Knowledge Base' });
    expect(helpHeading).toBeInTheDocument();

    expect(screen.getByText('The 4 Core Dashboard Screens')).toBeInTheDocument();
    expect(screen.getByText('The Six Deterministic Invariant Checks')).toBeInTheDocument();
    expect(screen.getByText('Mathematical Models & Formulas')).toBeInTheDocument();
    expect(screen.getByText('Frequently Asked Questions')).toBeInTheDocument();
  });
});
