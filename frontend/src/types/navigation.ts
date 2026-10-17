export type NavRoute =
  | 'overview'
  | 'runs'
  | 'run-detail'
  | 'new-eval'
  | 'catalog'
  | 'compare'
  | 'datasets'
  | 'task-analysis'
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
    title: 'EVALUATION WORKSPACE',
    items: [
      { id: 'overview', label: 'Overview' },
      { id: 'new-eval', label: 'New Evaluation' },
      { id: 'runs', label: 'Evaluation Runs' },
      { id: 'catalog', label: 'Model Catalog' },
      { id: 'compare', label: 'Compare Models' },
      { id: 'task-analysis', label: 'Task Analysis' },
      { id: 'datasets', label: 'Datasets' },
      { id: 'evaluators', label: 'Evaluators' },
      { id: 'reports', label: 'Reports' },
    ],
  },
  {
    title: 'ADVANCED TRACES',
    items: [
      { id: 'rag', label: 'RAG Evaluation' },
      { id: 'agents', label: 'Agent Evaluation' },
      { id: 'settings', label: 'Settings' },
    ],
  },
];
