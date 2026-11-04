// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { renderToString } from 'react-dom/server';
import App from '../App';
import { EvaluationResultsWorkspace } from '../pages/EvaluationResultsWorkspace';

describe('App & Evaluation Workspace Integration Render Tests', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders App without crashing on default route', () => {
    window.history.pushState({}, '', '/');
    const html = renderToString(React.createElement(App));
    expect(html).toBeDefined();
    expect(html).toContain('EvalForge20');
    expect(html).toContain('Playground');
    expect(html.length).toBeGreaterThan(1000);
  });

  it('renders App with navigation sidebar items intact', () => {
    window.history.pushState({}, '', '/');
    const html = renderToString(React.createElement(App));
    expect(html).toContain('Evaluation Results');
    expect(html).toContain('Experiments');
    expect(html).toContain('Models');
    expect(html).toContain('Benchmarks');
    expect(html).toContain('Datasets');
    expect(html).toContain('Leaderboard');
    expect(html).toContain('Settings');
  });

  it('renders App when navigating to an evaluation route /evaluations/exec-999', () => {
    window.history.pushState({}, '', '/evaluations/exec-999');
    const html = renderToString(React.createElement(App));
    expect(html).toBeDefined();
    expect(html).toContain('EvalForge20');
  });

  it('renders EvaluationResultsWorkspace loading state for active run', () => {
    const html = renderToString(
      React.createElement(EvaluationResultsWorkspace, {
        runId: 'exec-loading-1',
        onBackToPlayground: () => {},
      })
    );
    expect(html).toContain('Loading Evaluation Results');
    expect(html).toContain('exec-loading-1');
  });

  it('renders EvaluationResultsWorkspace empty state when no run is specified', () => {
    const html = renderToString(
      React.createElement(EvaluationResultsWorkspace, {
        runId: null,
        onBackToPlayground: () => {},
      })
    );
    expect(html).toBeDefined();
  });
});
