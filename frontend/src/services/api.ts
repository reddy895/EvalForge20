/**
 * Centralized API service layer.
 * Re-exports the typed API client and domain types for feature modules.
 */
import { api, apiClient } from '../api/client';
export * from '../api/types';

export { api, apiClient };
export default api;
