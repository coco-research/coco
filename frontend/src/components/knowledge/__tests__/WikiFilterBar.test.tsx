import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { WikiFilterBar, articleTypeBadge, type WikiFilters } from '../WikiFilterBar';

const defaults: WikiFilters = { articleType: '', entityType: '', minConfidence: 0 };

function setup(overrides?: Partial<WikiFilters>) {
  const onChange = vi.fn();
  const filters = { ...defaults, ...overrides };
  const result = render(<WikiFilterBar filters={filters} onChange={onChange} />);
  return { onChange, filters, ...result };
}

describe('WikiFilterBar', () => {
  it('renders all article type pills', () => {
    setup();
    expect(screen.getByRole('button', { name: 'Entity' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Product' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Meeting' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Graph Insight' })).toBeInTheDocument();
  });

  it('toggles article type on click', async () => {
    const user = userEvent.setup();
    const { onChange } = setup();

    await user.click(screen.getByRole('button', { name: 'Meeting' }));
    expect(onChange).toHaveBeenCalledWith({ ...defaults, articleType: 'meeting' });
  });

  it('deselects article type when clicking the active one', async () => {
    const user = userEvent.setup();
    const { onChange } = setup({ articleType: 'meeting' });

    await user.click(screen.getByRole('button', { name: 'Meeting' }));
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ articleType: '' }));
  });

  it('changes entity type via dropdown', async () => {
    const user = userEvent.setup();
    const { onChange } = setup();

    await user.selectOptions(screen.getByRole('combobox'), 'person');
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ entityType: 'person' }));
  });

  it('updates confidence slider', () => {
    const { onChange } = setup();
    const slider = screen.getByRole('slider');

    // fireEvent works better for range inputs than userEvent
    slider.focus();
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!.call(slider, '50');
    slider.dispatchEvent(new Event('change', { bubbles: true }));

    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ minConfidence: 50 }));
  });

  it('shows "Any" when confidence is 0', () => {
    setup({ minConfidence: 0 });
    expect(screen.getByText('Any')).toBeInTheDocument();
  });

  it('shows percentage when confidence > 0', () => {
    setup({ minConfidence: 45 });
    expect(screen.getByText('45%')).toBeInTheDocument();
  });

  it('hides clear button when no filters active', () => {
    setup();
    expect(screen.queryByText(/Clear/)).not.toBeInTheDocument();
  });

  it('shows clear button with active count', () => {
    setup({ articleType: 'entity', entityType: 'person', minConfidence: 50 });
    expect(screen.getByText('Clear (3)')).toBeInTheDocument();
  });

  it('clear button resets all filters', async () => {
    const user = userEvent.setup();
    const { onChange } = setup({ articleType: 'entity', minConfidence: 30 });

    await user.click(screen.getByText('Clear (2)'));
    expect(onChange).toHaveBeenCalledWith({ articleType: '', entityType: '', minConfidence: 0, project: '' });
  });
});

describe('articleTypeBadge', () => {
  it('returns label and class for known types', () => {
    const badge = articleTypeBadge('meeting');
    expect(badge.label).toBe('Meeting');
    expect(badge.className).toContain('blue');
  });

  it('returns teal badge for product type', () => {
    const badge = articleTypeBadge('product');
    expect(badge.label).toBe('Product');
    expect(badge.className).toContain('teal');
  });

  it('falls back for unknown types', () => {
    const badge = articleTypeBadge('custom_unknown');
    expect(badge.label).toBe('custom_unknown');
    expect(badge.className).toContain('muted-foreground');
  });
});
