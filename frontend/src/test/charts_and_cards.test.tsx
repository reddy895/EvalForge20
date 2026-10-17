import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MetricCard } from '../components/dashboard/MetricCard'
import { ScoreHistoryChart } from '../components/dashboard/ScoreHistoryChart'
import type { RunSummary } from '../api/types'

describe('MetricCard component', () => {
  it('renders title, tabular value, unit, and footer', () => {
    render(
      <MetricCard
        title="Average Score"
        value="89.4"
        unit="%"
        footer="Across 24 completed runs"
      />
    )
    expect(screen.getByText('Average Score')).toBeInTheDocument()
    expect(screen.getByText('89.4')).toBeInTheDocument()
    expect(screen.getByText('%')).toBeInTheDocument()
    expect(screen.getByText('Across 24 completed runs')).toBeInTheDocument()
  })

  it('renders dash fallback when value is null or undefined', () => {
    render(<MetricCard title="Failure Rate" value={null} />)
    expect(screen.getByText('—')).toBeInTheDocument()
  })

  it('renders loading skeleton when isLoading is true', () => {
    const { container } = render(<MetricCard title="Total Runs" value={10} isLoading />)
    expect(container.querySelector('.metric-card-skeleton')).toBeInTheDocument()
  })
})

describe('ScoreHistoryChart component', () => {
  it('renders honest empty state when runs array is empty or insufficient', () => {
    render(<ScoreHistoryChart runs={[]} />)
    expect(
      screen.getByText('Insufficient historical runs to compute score progression.')
    ).toBeInTheDocument()
  })

  it('renders SVG chart with data points when valid runs exist', () => {
    const runs: RunSummary[] = [
      {
        run_id: 'run-1',
        name: 'Evaluation Alpha',
        status: 'completed',
        pass_rate: 0.82,
        started_at: '2026-03-29T10:00:00Z',
        completed_at: '2026-03-29T10:02:00Z',
        total_cases: 10,
        completed_cases: 8,
        failed_cases: 2,
        error_message: null,
      },
      {
        run_id: 'run-2',
        name: 'Evaluation Beta',
        status: 'completed',
        pass_rate: 0.91,
        started_at: '2026-03-30T10:00:00Z',
        completed_at: '2026-03-30T10:02:00Z',
        total_cases: 10,
        completed_cases: 9,
        failed_cases: 1,
        error_message: null,
      },
    ]

    const { container } = render(<ScoreHistoryChart runs={runs} />)
    const svg = container.querySelector('.chart-svg')
    expect(svg).toBeInTheDocument()
    const points = container.querySelectorAll('.chart-point')
    expect(points.length).toBe(2)
  })
})
