/**
 * Comparisons feature module.
 * Provides multi-model side-by-side matrices, regression detection, and delta diffing.
 */
export { CompareMetricsTable } from '../../components/compare/CompareMetricsTable';
export { CompareSelector } from '../../components/compare/CompareSelector';
export { RegressionInspector } from '../../components/compare/RegressionInspector';
export { useComparison } from '../../hooks/useComparison';
export type { ComparisonResult, MultiRunComparisonMatrix } from '../../api/types';
