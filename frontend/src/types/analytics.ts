/**
 * Frontend analytics and telemetry TypeScript definitions.
 */

export interface CommitHistoryItem {
  hash: string;
  date: string;
  author: string;
  message: string;
}

export interface DayActivity {
  date: string;
  count: number;
  level: number;
  sample_commits?: CommitHistoryItem[];
}

export interface CommitTelemetry {
  target_commits: number;
  total_verified_commits: number;
  target_achieved: boolean;
  target_progress_percent: number;
  status_label: string;
  source: string;
  daily_activity: DayActivity[];
  author_distribution: Record<string, number>;
}
