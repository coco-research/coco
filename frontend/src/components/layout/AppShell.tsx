import { Outlet } from 'react-router-dom';
import { Search } from 'lucide-react';
import { Sidebar } from './Sidebar';
import { Breadcrumbs } from '../shared/Breadcrumbs';
import { NotificationDropdown } from '../shared/NotificationDropdown';
import { useSSEStatus } from '../shared/NotificationProvider';

function ConnectionBanner() {
  const status = useSSEStatus();

  if (status === 'connected' || status === 'connecting') return null;

  const isFailed = status === 'failed';

  return (
    <div
      className={`px-4 py-2 text-center text-xs font-medium ${
        isFailed
          ? 'bg-destructive/10 text-destructive border-b border-destructive/20'
          : 'bg-warning/10 text-warning border-b border-warning/20'
      }`}
    >
      {isFailed
        ? 'Connection lost — could not reconnect. Please refresh the page.'
        : 'Connection lost — retrying...'}
    </div>
  );
}

export function AppShell() {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex-1 ml-60 flex flex-col">
        {/* Offline banner */}
        <ConnectionBanner />

        {/* Top header bar */}
        <header className="sticky top-0 z-30 bg-background/80 backdrop-blur-sm border-b border-border px-6 py-3 flex items-center justify-between">
          <Breadcrumbs />
          <div className="flex items-center gap-2">
            <button className="flex items-center gap-2 px-3 py-1.5 text-sm text-muted-foreground bg-secondary border border-border rounded-md hover:bg-accent/50 transition-colors">
              <Search size={14} />
              <span className="text-xs">Search</span>
              <kbd className="ml-1 text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded font-mono">
                ⌘K
              </kbd>
            </button>
            <NotificationDropdown />
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 p-6 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
