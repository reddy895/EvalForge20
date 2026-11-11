// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { renderToString } from 'react-dom/server';
import { DatasetsView } from '../pages/DatasetsView';

describe('DatasetsView render states', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the dataset workspace with import and create controls', () => {
    const html = renderToString(React.createElement(DatasetsView));
    expect(html).toContain('Evaluation Datasets');
    expect(html).toContain('Available Datasets');
    expect(html).toContain('Import');
    expect(html).toContain('New');
    expect(html).toContain('Refresh');
  });

  it('renders an accessible selection placeholder before data loads', () => {
    const html = renderToString(React.createElement(DatasetsView));
    expect(html).toContain('No Dataset Selected');
  });
});
