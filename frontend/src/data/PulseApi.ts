import { PulseNote, Theme, SampleReview, RunState, ImportSummary, ScenarioType } from './types';

export interface PulseApi {
  getPulse(week?: string, scenario?: ScenarioType): Promise<PulseNote>;
  getThemes(week?: string, scenario?: ScenarioType): Promise<Theme[]>;
  getThemeSamples(themeId: string): Promise<SampleReview[]>;
  getRun(week?: string, scenario?: ScenarioType): Promise<RunState>;
  startRun(week?: string): Promise<RunState>;
  getImportSummary(scenario?: ScenarioType): Promise<ImportSummary>;
  uploadReviews(file: File): Promise<{ success: boolean; rowsAdded: number; message: string }>;
}
