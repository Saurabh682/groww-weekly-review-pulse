import { afterEach, describe, it, expect, vi } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FakeApi, app } from './fakeApi';
import { openRoute } from './openRoute';

const renderWithRouter = (initialRoute: string) => {
  new FakeApi().apps(app('groww', 'Groww')).install();
  return openRoute(initialRoute);
};

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe('Frontend Screens Suite', () => {
  it('WeeklyPulsePage renders score, top 3 themes, verbatim quotes, and action ideas', async () => {
    renderWithRouter('/sample');

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

  it('HelpPage renders features, sample scenarios and questions', async () => {
    renderWithRouter('/help');

    const helpHeading = await screen.findByRole('heading', { level: 1, name: 'Help' });
    expect(helpHeading).toBeInTheDocument();

    expect(screen.getByRole('heading', { level: 2, name: 'Features and how they work' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Sample page scenarios' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Frequently asked questions' })).toBeInTheDocument();
    expect(screen.queryByText('The Six Deterministic Invariant Checks')).toBeNull();
  });

  it.each([
    ['/sample', 'Weekly Review Pulse'],
    ['/themes', 'Themes Explorer'],
    ['/run', 'Run & Publish Pipeline'],
    ['/import', 'Data Ingestion & Hygiene'],
    ['/help', 'Help'],
  ])('test_UIC_13_every_control_has_a_name: %s', async (route, title) => {
    renderWithRouter(route);
    await screen.findByRole('heading', { level: 1, name: title }, { timeout: 2000 });
    for (const field of screen.queryAllByRole('textbox')) await userEvent.type(field, 'a');
    const controls = ['button', 'textbox', 'combobox', 'link'].flatMap((role) => screen.queryAllByRole(role));
    expect(controls.length).toBeGreaterThan(3);
    controls.forEach((control) => expect(control, control.outerHTML.slice(0, 160)).toHaveAccessibleName());
  });

  it.each([
    ['/sample', 'Weekly Review Pulse'],
    ['/themes', 'Themes Explorer'],
    ['/run', 'Run & Publish Pipeline'],
    ['/import', 'Data Ingestion & Hygiene'],
    ['/help', 'Help'],
  ])('test_UIC_14_headings_never_skip_a_level: %s', async (route, title) => {
    renderWithRouter(route);
    await screen.findByRole('heading', { level: 1, name: title }, { timeout: 2000 });
    const levels = screen.getAllByRole('heading').map((heading) => Number(heading.tagName.slice(1)));
    const skips = levels.flatMap((level, i) => (i > 0 && level > levels[i - 1] + 1 ? [`h${levels[i - 1]} then h${level}`] : []));
    expect(skips, 'A heading may go at most one level deeper than the heading before it.').toEqual([]);
  });
});
