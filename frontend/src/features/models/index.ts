/**
 * Models feature module.
 * Provides model selection, dynamic discovery, and provider configuration components.
 */
export { ModelSelector } from '../../components/eval-flow/ModelSelector';
export { StepProvider } from '../../components/eval-flow/StepProvider';
export { useModels } from '../../hooks/useModels';
export type { DetailedModel, CatalogModel, OllamaDiagnosticReport } from '../../api/types';
