import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { DataTable, type Column } from '../components/ui/DataTable'

describe('Button component', () => {
  it('renders children correctly', () => {
    render(<Button>Run Evaluation</Button>)
    expect(screen.getByText('Run Evaluation')).toBeInTheDocument()
  })

  it('handles click events', () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick}>Click Me</Button>)
    fireEvent.click(screen.getByText('Click Me'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('applies primary variant when specified and secondary by default', () => {
    const { container: def } = render(<Button>Default</Button>)
    expect(def.querySelector('.btn-secondary')).toBeInTheDocument()

    const { container: pri } = render(<Button variant="primary">Primary</Button>)
    expect(pri.querySelector('.btn-primary')).toBeInTheDocument()
  })

  it('applies secondary, danger, and ghost variants', () => {
    const { container: sec } = render(<Button variant="secondary">Sec</Button>)
    expect(sec.querySelector('.btn-secondary')).toBeInTheDocument()

    const { container: dan } = render(<Button variant="danger">Dan</Button>)
    expect(dan.querySelector('.btn-danger')).toBeInTheDocument()

    const { container: gho } = render(<Button variant="ghost">Gho</Button>)
    expect(gho.querySelector('.btn-ghost')).toBeInTheDocument()
  })

  it('disables button when disabled or loading prop is set', () => {
    const handleClick = vi.fn()
    const { rerender } = render(<Button disabled onClick={handleClick}>Disabled</Button>)
    const button = screen.getByRole('button') as HTMLButtonElement
    expect(button.disabled).toBe(true)
    fireEvent.click(button)
    expect(handleClick).not.toHaveBeenCalled()

    rerender(<Button loading onClick={handleClick}>Loading</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
  })
})

describe('Badge component', () => {
  it('renders with default variant and children', () => {
    render(<Badge>v1.0.0</Badge>)
    expect(screen.getByText('v1.0.0')).toBeInTheDocument()
    expect(screen.getByText('v1.0.0')).toHaveClass('badge-neutral')
  })

  it('supports success and error status variants', () => {
    const { rerender } = render(<Badge variant="success">COMPLETED</Badge>)
    expect(screen.getByText('COMPLETED')).toHaveClass('badge-success')

    rerender(<Badge variant="error">FAILED</Badge>)
    expect(screen.getByText('FAILED')).toHaveClass('badge-error')
  })

  it('supports dot indicator', () => {
    const { container } = render(<Badge variant="success" showDot>Online</Badge>)
    expect(container.querySelector('.badge-dot')).toBeInTheDocument()
  })
})

interface TestItem {
  id: string
  name: string
  score: number
}

describe('DataTable component', () => {
  const columns: Column<TestItem>[] = [
    { key: 'id', header: 'ID', sortable: true },
    { key: 'name', header: 'Model Name' },
    {
      key: 'score',
      header: 'Score',
      align: 'right',
      render: (item) => `${(item.score * 100).toFixed(1)}%`,
    },
  ]

  const data: TestItem[] = [
    { id: 'run_1', name: 'llama3:8b', score: 0.885 },
    { id: 'run_2', name: 'mistral:7b', score: 0.923 },
  ]

  it('renders columns and data rows accurately', () => {
    render(<DataTable columns={columns} data={data} keyExtractor={(item) => item.id} />)
    expect(screen.getByText('llama3:8b')).toBeInTheDocument()
    expect(screen.getByText('mistral:7b')).toBeInTheDocument()
    expect(screen.getByText('88.5%')).toBeInTheDocument()
    expect(screen.getByText('92.3%')).toBeInTheDocument()
  })

  it('displays honest empty state when no data is provided', () => {
    render(
      <DataTable
        columns={columns}
        data={[]}
        keyExtractor={(item) => item.id}
        emptyMessage="No evaluations found in database."
      />
    )
    expect(screen.getByText('No evaluations found in database.')).toBeInTheDocument()
  })

  it('triggers onSort when sortable header is clicked', () => {
    const handleSort = vi.fn()
    render(
      <DataTable
        columns={columns}
        data={data}
        keyExtractor={(item) => item.id}
        initialSortKey="id"
        initialSortDir="asc"
        onSort={handleSort}
      />
    )
    fireEvent.click(screen.getByText('ID'))
    expect(handleSort).toHaveBeenCalledWith('id')
  })
})
