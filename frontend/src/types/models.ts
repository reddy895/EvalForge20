/**
 * Frontend model catalog and pricing TypeScript definitions.
 */

export interface HardwareMemorySpecs {
  min_ram_gb: number;
  recommended_ram_gb: number;
  fits_in_8gb: boolean;
  fits_in_16gb: boolean;
}

export interface PricingRates {
  input_per_m: number;
  output_per_m: number;
  is_free_local: boolean;
}

export interface ModelDetailItem {
  id: string;
  name: string;
  provider: string;
  is_local: boolean;
  is_installed: boolean;
  context_window: number;
  hardware: HardwareMemorySpecs;
  pricing: PricingRates;
  recommended_tasks: string[];
}
