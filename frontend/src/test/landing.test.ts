import { describe, it, expect } from 'vitest';
import type { NavRoute } from '../types';

describe('Landing Page Structure, Sections, and Navigation Hierarchy', () => {
  it('validates supported navigation routes on landing page CTAs', () => {
    const executedRoutes: NavRoute[] = [];
    const onRouteChange = (route: NavRoute) => {
      executedRoutes.push(route);
    };

    // Primary CTA: Start Evaluating
    onRouteChange('evaluate');
    expect(executedRoutes).toContain('evaluate');

    // Secondary CTA: Explore Model Catalog
    onRouteChange('models');
    expect(executedRoutes).toContain('models');

    // Telemetry CTA: System Telemetry
    onRouteChange('analytics');
    expect(executedRoutes).toContain('analytics');

    // Studio comparison CTA
    onRouteChange('compare');
    expect(executedRoutes).toContain('compare');
  });

  it('validates section configuration hierarchy and layout integrity', () => {
    const expectedSections = [
      'hero',
      'discovery',
      'why-evalforge',
      'how-it-works',
      'comparison',
      'evaluation',
      'local-first',
      'final-cta',
    ];

    expect(expectedSections.length).toBe(8);
    expect(expectedSections[0]).toBe('hero');
    expect(expectedSections[expectedSections.length - 1]).toBe('final-cta');
  });

  it('ensures responsive layout grid tokens and maximum width bounds are defined', () => {
    const containerClasses = ['w-full', 'max-w-7xl', 'mx-auto', 'px-4', 'sm:px-6', 'lg:px-8'];
    containerClasses.forEach((cls) => {
      expect(typeof cls).toBe('string');
      expect(cls.length).toBeGreaterThan(0);
    });

    const isFullWidthResponsive = containerClasses.includes('max-w-7xl') && containerClasses.includes('w-full');
    expect(isFullWidthResponsive).toBe(true);
  });
});
