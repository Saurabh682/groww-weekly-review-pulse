import { PulseApi } from './PulseApi';
import { PulseNote, Theme, SampleReview, RunState, ImportSummary, ScenarioType } from './types';
import { FIXTURE_PULSE_NOTE, FIXTURE_THEMES } from './fixtures/pulseNote';
import { SAMPLE_REVIEWS } from './fixtures/reviews';
import { FIXTURE_RUN_STATE, FAILED_RUN_STATE } from './fixtures/runs';
import { FIXTURE_IMPORT_SUMMARY, LOW_COVERAGE_IMPORT_SUMMARY } from './fixtures/imports';

function getUrlScenario(): ScenarioType {
  if (typeof window === 'undefined') return 'ok';
  const params = new URLSearchParams(window.location.search);
  const scenario = params.get('scenario') as ScenarioType | null;
  if (scenario && ['ok', 'empty', 'error', 'validation-failed', 'low-coverage'].includes(scenario)) {
    return scenario;
  }
  return 'ok';
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export class MockPulseApi implements PulseApi {
  private latencyMs: number;

  constructor(latencyMs = 350) {
    this.latencyMs = latencyMs;
  }

  async getPulse(_week?: string, explicitScenario?: ScenarioType): Promise<PulseNote> {
    await delay(this.latencyMs);
    const scenario = explicitScenario || getUrlScenario();

    if (scenario === 'error') {
      throw new Error('Failed to retrieve pulse data from mock repository: 500 Internal Server Error');
    }

    if (scenario === 'empty') {
      return {
        ...FIXTURE_PULSE_NOTE,
        totalReviews: 0,
        avgRating: 0,
        pulseScore: 0,
        moodLabel: 'No Data',
        topThemes: [],
        allThemes: [],
        quotes: [],
        actions: [],
        wordCount: 0,
        checks: [],
      };
    }

    return FIXTURE_PULSE_NOTE;
  }

  async getThemes(_week?: string, explicitScenario?: ScenarioType): Promise<Theme[]> {
    await delay(this.latencyMs);
    const scenario = explicitScenario || getUrlScenario();

    if (scenario === 'error') {
      throw new Error('Failed to fetch themes: Cluster engine service unavailable');
    }

    if (scenario === 'empty') {
      return [];
    }

    return FIXTURE_THEMES;
  }

  async getThemeSamples(themeId: string): Promise<SampleReview[]> {
    await delay(this.latencyMs / 2);
    const filtered = SAMPLE_REVIEWS.filter(r => r.themeId === themeId);
    return filtered.length > 0 ? filtered : SAMPLE_REVIEWS.slice(0, 5);
  }

  async getRun(_week?: string, explicitScenario?: ScenarioType): Promise<RunState> {
    await delay(this.latencyMs);
    const scenario = explicitScenario || getUrlScenario();

    if (scenario === 'error') {
      throw new Error('Pipeline execution failed: Orchestrator connection timeout');
    }

    if (scenario === 'validation-failed') {
      return FAILED_RUN_STATE;
    }

    return FIXTURE_RUN_STATE;
  }

  async startRun(_week?: string): Promise<RunState> {
    await delay(1200);
    const scenario = getUrlScenario();
    if (scenario === 'validation-failed') {
      return FAILED_RUN_STATE;
    }
    return FIXTURE_RUN_STATE;
  }

  async getImportSummary(explicitScenario?: ScenarioType): Promise<ImportSummary> {
    await delay(this.latencyMs);
    const scenario = explicitScenario || getUrlScenario();

    if (scenario === 'error') {
      throw new Error('Failed to query hygiene metadata store');
    }

    if (scenario === 'low-coverage') {
      return LOW_COVERAGE_IMPORT_SUMMARY;
    }

    if (scenario === 'empty') {
      return {
        imported: 0,
        duplicatesRemoved: 0,
        lowInfoExcluded: 0,
        piiRedacted: 0,
        weeklyVolume: [],
        coverageWeeks: 0,
        history: [],
      };
    }

    return FIXTURE_IMPORT_SUMMARY;
  }

  async uploadReviews(file: File): Promise<{ success: boolean; rowsAdded: number; message: string }> {
    await delay(800);
    if (!file.name.endsWith('.csv') && !file.name.endsWith('.json')) {
      throw new Error('Unsupported file format. Please upload a standard CSV or JSON export.');
    }
    return {
      success: true,
      rowsAdded: 662,
      message: `Successfully processed ${file.name}. 662 clean reviews ready for clustering.`,
    };
  }
}

export const pulseApi = new MockPulseApi();
