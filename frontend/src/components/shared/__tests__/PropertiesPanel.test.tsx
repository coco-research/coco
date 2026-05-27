import { useState } from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { PropertiesPanel } from '../PropertiesPanel';

function Harness({
  initialOpen = false,
  onClose,
  width,
}: {
  initialOpen?: boolean;
  onClose?: () => void;
  width?: number | 'sm' | 'md' | 'lg';
}) {
  const [open, setOpen] = useState(initialOpen);
  return (
    <>
      <button onClick={() => setOpen(true)}>open-panel</button>
      <PropertiesPanel
        open={open}
        onClose={() => {
          setOpen(false);
          onClose?.();
        }}
        title="Agent Details"
        subtitle="status: running"
        width={width}
      >
        <div data-testid="panel-body">body-content</div>
      </PropertiesPanel>
    </>
  );
}

describe('PropertiesPanel', () => {
  it('does not render content when closed', () => {
    render(<Harness />);
    expect(screen.queryByTestId('panel-body')).toBeNull();
  });

  it('renders title, subtitle, and children when open', async () => {
    const user = userEvent.setup();
    render(<Harness />);
    await user.click(screen.getByText('open-panel'));

    expect(screen.getByText('Agent Details')).toBeInTheDocument();
    expect(screen.getByText('status: running')).toBeInTheDocument();
    expect(screen.getByTestId('panel-body')).toHaveTextContent('body-content');
  });

  it('invokes onClose when the close button is clicked', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<Harness initialOpen onClose={onClose} />);

    expect(screen.getByTestId('panel-body')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /close panel/i }));
    expect(onClose).toHaveBeenCalledTimes(1);
    expect(screen.queryByTestId('panel-body')).toBeNull();
  });

  it('invokes onClose on Escape key', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<Harness initialOpen onClose={onClose} />);

    expect(screen.getByTestId('panel-body')).toBeInTheDocument();
    await user.keyboard('{Escape}');
    expect(onClose).toHaveBeenCalledTimes(1);
    expect(screen.queryByTestId('panel-body')).toBeNull();
  });

  it('accepts a numeric width prop', async () => {
    const user = userEvent.setup();
    render(<Harness width={520} />);
    await user.click(screen.getByText('open-panel'));

    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveStyle({ width: '520px' });
  });

  it('accepts a legacy preset width prop', async () => {
    const user = userEvent.setup();
    render(<Harness width="lg" />);
    await user.click(screen.getByText('open-panel'));

    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveStyle({ width: '480px' });
  });
});
