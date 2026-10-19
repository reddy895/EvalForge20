import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Navigation } from '../app/Navigation';
import type { OllamaStatusReport } from '../types';

describe('Navigation component', () => {
  const mockStatusOnline: OllamaStatusReport = {
    is_reachable: true,
    base_url: 'http://localhost:11434',
    installed_models: ['llama3.2:3b'],
    models_count: 1,
    status_label: 'online',
    setup_instructions: [],
  };

  const mockStatusOffline: OllamaStatusReport = {
    is_reachable: false,
    base_url: 'http://localhost:11434',
    installed_models: [],
    models_count: 0,
    status_label: 'offline',
    setup_instructions: ['Run: ollama serve'],
  };

  it('renders brand title and all 5 primary minimal navigation tabs', () => {
    const onRouteChange = vi.fn();
    render(
      <Navigation
        activeRoute="catalog"
        onRouteChange={onRouteChange}
        ollamaStatus={mockStatusOnline}
      />
    );

    expect(screen.getByText('EvalForge')).toBeInTheDocument();
    expect(screen.getByText('Explore Models')).toBeInTheDocument();
    expect(screen.getByText('Compare Models')).toBeInTheDocument();
    expect(screen.getByText('Evaluate Locally')).toBeInTheDocument();
    expect(screen.getByText('Evaluation History')).toBeInTheDocument();
    expect(screen.getByText('Settings & Daemon')).toBeInTheDocument();
  });

  it('triggers route changes when navigation tabs are clicked', () => {
    const onRouteChange = vi.fn();
    render(
      <Navigation
        activeRoute="catalog"
        onRouteChange={onRouteChange}
        ollamaStatus={mockStatusOnline}
      />
    );

    fireEvent.click(screen.getByText('Compare Models'));
    expect(onRouteChange).toHaveBeenCalledWith('compare');

    fireEvent.click(screen.getByText('Evaluate Locally'));
    expect(onRouteChange).toHaveBeenCalledWith('evaluate');

    fireEvent.click(screen.getByText('Evaluation History'));
    expect(onRouteChange).toHaveBeenCalledWith('history');

    fireEvent.click(screen.getByText('Settings & Daemon'));
    expect(onRouteChange).toHaveBeenCalledWith('settings');
  });

  it('displays online daemon indicator when Ollama is running', () => {
    render(
      <Navigation
        activeRoute="catalog"
        onRouteChange={vi.fn()}
        ollamaStatus={mockStatusOnline}
      />
    );

    expect(screen.getByText(/1 Installed/i)).toBeInTheDocument();
  });

  it('displays offline indicator when Ollama is offline', () => {
    render(
      <Navigation
        activeRoute="catalog"
        onRouteChange={vi.fn()}
        ollamaStatus={mockStatusOffline}
      />
    );

    expect(screen.getByText(/Offline/i)).toBeInTheDocument();
  });
});
