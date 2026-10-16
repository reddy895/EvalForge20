export type NavRoute =
  | 'overview'
  | 'runs'
  | 'run-detail'
  | 'new-eval'
  | 'compare'
  | 'datasets'
  | 'providers'
  | 'evaluators'
  | 'reports'
  | 'rag'
  | 'agents'
  | 'settings';

export interface NavItemConfig {
  id: NavRoute;
  label: string;
  badge?: string;
  badgeType?: 'default' | 'accent' | 'success';
}

export interface NavSectionConfig {
  title: string;
  items: NavItemConfig[];
}

export const NAVIGATION_STRUCTURE: NavSectionConfig[] = [
  {
    title: 'WORKSPACE',
    items: [
      { id: 'overview', label: 'Overview' },
      { id: 'runs', label: 'Evaluation Runs' },
      { id: 'compare', label: 'Compare Runs' },
      { id: 'datasets', label: 'Datasets' },
      { id: 'providers', label: 'Models & Providers' },
      { id: 'evaluators', label: 'Evaluators' },
      { id: 'reports', label: 'Reports' },
    ],
  },
  {
    title: 'DEVELOPMENT',
    items: [
      { id: 'rag', label: 'RAG Evaluation' },
      { id: 'agents', label: 'Agent Evaluation' },
      { id: 'settings', label: 'Settings' },
    ],
  },
];
