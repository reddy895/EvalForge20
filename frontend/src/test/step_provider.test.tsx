import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { StepProvider } from '../components/eval-flow/StepProvider';
import { api } from '../api/client';
import type { TargetConfiguration } from '../api/types';

describe('StepProvider Component', () => {
  const mockTarget: TargetConfiguration = {
    target_name: 'test-target',
    target_type: 'ollama',
    provider_name: 'ollama',
    model_identifier: 'qwen2.5:3b',
    base_url: 'http://localhost:11434',
    temperature: 0.0,
    max_tokens: null,
    timeout_seconds: 60.0,
    extra_params: {},
  };

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('displays online status and installed models when Ollama is running', async () => {
    vi.spyOn(api, 'getOllamaStatus').mockResolvedValueOnce({
      connected: true,
      is_reachable: true,
      base_url: 'http://localhost:11434',
      version: '0.3.14',
      models: ['qwen2.5:3b', 'llama3.2:3b'],
      installed_models: ['qwen2.5:3b', 'llama3.2:3b'],
      models_count: 2,
      error_message: null,
      latency_ms: 14.2,
      status_code: 200,
      status_label: 'online',
      setup_instructions: [],
    });

    vi.spyOn(api, 'listModels').mockResolvedValueOnce([
      {
        name: 'qwen2.5:3b',
        model: 'qwen2.5:3b',
        modified_at: '2026-03-29',
        size: 1900000000,
        digest: 'hash1',
        details: { parameter_size: '3.1B', quantization_level: 'Q4_K_M' },
      },
      {
        name: 'llama3.2:3b',
        model: 'llama3.2:3b',
        modified_at: '2026-03-29',
        size: 2000000000,
        digest: 'hash2',
        details: { parameter_size: '3.2B', quantization_level: 'Q4_K_M' },
      },
    ]);

    const onChange = vi.fn();
    const onValidChange = vi.fn();

    render(
      <StepProvider target={mockTarget} onChange={onChange} onValidChange={onValidChange} />
    );

    await waitFor(() => {
      expect(screen.getByText(/Online \(0.3.14\)/i)).toBeInTheDocument();
      expect(screen.getByText(/2 installed · 14.2ms/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/Select Installed Model/i)).toBeInTheDocument();
  });

  it('displays offline status and troubleshooting commands when Ollama is not reachable', async () => {
    vi.spyOn(api, 'getOllamaStatus').mockResolvedValueOnce({
      connected: false,
      is_reachable: false,
      base_url: 'http://localhost:11434',
      version: null,
      models: [],
      installed_models: [],
      models_count: 0,
      error_message: 'Connection refused',
      latency_ms: null,
      status_code: null,
      status_label: 'offline',
      setup_instructions: [],
    });

    const onChange = vi.fn();
    const onValidChange = vi.fn();

    render(
      <StepProvider target={mockTarget} onChange={onChange} onValidChange={onValidChange} />
    );

    await waitFor(() => {
      expect(screen.getByText(/Offline \(http:\/\/localhost:11434\)/i)).toBeInTheDocument();
      expect(screen.getByText(/Ollama Daemon Not Detected/i)).toBeInTheDocument();
      expect(screen.getByText(/ollama serve/i)).toBeInTheDocument();
    });
  });

  it('allows switching between installed dropdown and manual identifier input', async () => {
    vi.spyOn(api, 'getOllamaStatus').mockResolvedValueOnce({
      connected: true,
      is_reachable: true,
      base_url: 'http://localhost:11434',
      version: '0.3.14',
      models: ['qwen2.5:3b'],
      installed_models: ['qwen2.5:3b'],
      models_count: 1,
      error_message: null,
      latency_ms: 10,
      status_code: 200,
      status_label: 'online',
      setup_instructions: [],
    });

    vi.spyOn(api, 'listModels').mockResolvedValueOnce([
      {
        name: 'qwen2.5:3b',
        model: 'qwen2.5:3b',
        modified_at: '2026-03-29',
        size: 1900000000,
        digest: 'hash1',
        details: { parameter_size: '3.1B' },
      },
    ]);

    render(
      <StepProvider target={mockTarget} onChange={vi.fn()} onValidChange={vi.fn()} />
    );

    await waitFor(() => {
      expect(screen.getByText(/Enter custom identifier manually/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText(/Enter custom identifier manually/i));

    expect(screen.getByText(/Choose from installed models/i)).toBeInTheDocument();
  });
});
