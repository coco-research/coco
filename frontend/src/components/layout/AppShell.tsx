import { Outlet, useLocation } from 'react-router-dom';
import { Search } from 'lucide-react';
import { Sidebar, useSidebarCollapsed } from './Sidebar';
import { Breadcrumbs } from '../shared/Breadcrumbs';
import { NotificationDropdown } from '../shared/NotificationDropdown';
import { FloatingMic } from '../shared/FloatingMic';
import { useSSEStatus } from '../shared/NotificationProvider';
import { ShortcutsTour } from '../discovery/ShortcutsTour';

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
  const location = useLocation();
  const collapsed = useSidebarCollapsed();

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div
        className="flex-1 flex flex-col min-w-0 overflow-x-hidden transition-[margin-left] duration-200 ease-out"
        style={{ marginLeft: collapsed ? 48 : 240 }}
      >
        {/* Offline banner */}
        <ConnectionBanner />

        {/* Top header bar */}
        <header className="sticky top-0 z-30 bg-background/80 backdrop-blur-sm border-b border-border px-4 sm:px-5 lg:px-6 py-3 flex items-center justify-between gap-2">
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

        {/* Content — page transition on route change */}
        <main
          key={location.pathname}
          className="flex-1 p-4 sm:p-5 lg:p-6 max-w-7xl w-full mx-auto animate-page-enter"
        >
          <Outlet />
        </main>
      </div>

      {/* Floating mic for voice commands */}
      <FloatingMic />

      {/* First-run keyboard shortcuts tour (also opens on `?`) */}
      <ShortcutsTour />
    </div>
  );
}
