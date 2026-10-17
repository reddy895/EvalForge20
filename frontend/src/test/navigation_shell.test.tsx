import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Sidebar } from '../components/shell/Sidebar';
import { TopBar } from '../components/shell/TopBar';
import { MobileDrawer } from '../components/shell/MobileDrawer';

describe('Sidebar Navigation Shell', () => {
  it('renders brand title and primary navigation items', () => {
    const onRouteChange = vi.fn();
    render(<Sidebar currentRoute="overview" onRouteChange={onRouteChange} systemReady={true} />);

    expect(screen.getByText('EvalForge20')).toBeInTheDocument();
    expect(screen.getByText('Overview')).toBeInTheDocument();
    expect(screen.getAllByText('New Evaluation').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Evaluation Runs')).toBeInTheDocument();
    expect(screen.getByText('Model Catalog')).toBeInTheDocument();
    expect(screen.getByText('Compare Models')).toBeInTheDocument();
    expect(screen.getByText('Task Analysis')).toBeInTheDocument();
    expect(screen.getByText('Local Engine Ready')).toBeInTheDocument();
  });

  it('triggers route changes when navigation links are clicked', () => {
    const onRouteChange = vi.fn();
    render(<Sidebar currentRoute="overview" onRouteChange={onRouteChange} />);

    fireEvent.click(screen.getByText('Compare Models'));
    expect(onRouteChange).toHaveBeenCalledWith('compare');

    fireEvent.click(screen.getByText('Model Catalog'));
    expect(onRouteChange).toHaveBeenCalledWith('catalog');

    fireEvent.click(screen.getByText('Task Analysis'));
    expect(onRouteChange).toHaveBeenCalledWith('task-analysis');
  });

  it('indicates system disconnection when systemReady is false', () => {
    render(<Sidebar currentRoute="overview" onRouteChange={vi.fn()} systemReady={false} />);
    expect(screen.getByText('Backend Disconnected')).toBeInTheDocument();
  });
});

describe('TopBar Component', () => {
  it('renders workspace select and live Ollama daemon badge', () => {
    const onWorkspaceChange = vi.fn();
    const onToggleMenu = vi.fn();
    const onRefresh = vi.fn();

    render(
      <TopBar
        currentWorkspace="reddy895/EvalForge20"
        onWorkspaceChange={onWorkspaceChange}
        onToggleMobileMenu={onToggleMenu}
        ollamaConnected={true}
        onRefreshStatus={onRefresh}
      />
    );

    expect(screen.getByText('Ollama: 11434 (Active)')).toBeInTheDocument();

    const syncBtn = screen.getByRole('button', { name: /refresh system status/i });
    fireEvent.click(syncBtn);
    expect(onRefresh).toHaveBeenCalledTimes(1);

    const toggleBtn = screen.getByRole('button', { name: /open mobile navigation menu/i });
    fireEvent.click(toggleBtn);
    expect(onToggleMenu).toHaveBeenCalledTimes(1);
  });
});

describe('MobileDrawer Component', () => {
  it('renders when open and handles route selection and dismissal', () => {
    const onClose = vi.fn();
    const onRouteChange = vi.fn();

    const { rerender } = render(
      <MobileDrawer
        isOpen={false}
        onClose={onClose}
        currentRoute="overview"
        onRouteChange={onRouteChange}
      />
    );

    expect(screen.queryByRole('dialog')).not.toHaveClass('open');

    rerender(
      <MobileDrawer
        isOpen={true}
        onClose={onClose}
        currentRoute="overview"
        onRouteChange={onRouteChange}
      />
    );

    expect(screen.getByRole('dialog')).toHaveClass('open');

    const datasetsBtn = screen.getByRole('button', { name: /datasets/i });
    fireEvent.click(datasetsBtn);
    expect(onRouteChange).toHaveBeenCalledWith('datasets');
    expect(onClose).toHaveBeenCalled();
  });
});
