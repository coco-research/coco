import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppShell } from './components/layout/AppShell';
import { CommandPalette } from './components/shared/CommandPalette';
import { KeyboardShortcuts } from './components/shared/KeyboardShortcuts';
import { CocoOrb } from './components/shared/CocoOrb';
import { ErrorBoundary } from './components/shared/ErrorBoundary';
import { ToastProvider } from './components/shared/Toast';
import { NotificationProvider } from './components/shared/NotificationProvider';
import { ScopeProvider } from './context/ScopeContext';
import { useDesktopNotificationListener } from './hooks/useDesktopNotifications';
import { useVoiceCommands } from './hooks/useVoiceCommands';

// Eager: lightweight landing + dashboard (first paint)
import HomePage from './pages/HomePage';
import DashboardPage from './pages/DashboardPage';

// Lazy: everything else splits into separate chunks
const ProjectsPage = lazy(() => import('./pages/ProjectsPage'));
const ProjectDetailPage = lazy(() => import('./pages/ProjectDetailPage'));
const AgentsPage = lazy(() => import('./pages/AgentsPage'));
const KnowledgePage = lazy(() => import('./pages/KnowledgePage'));
const InboxPage = lazy(() => import('./pages/InboxPage'));
const TodosPage = lazy(() => import('./pages/TodosPage'));
const GoalsPage = lazy(() => import('./pages/GoalsPage'));
const ChatPage = lazy(() => import('./pages/ChatPage'));
const CostsPage = lazy(() => import('./pages/CostsPage'));
const ActivityPage = lazy(() => import('./pages/ActivityPage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));
const TreePage = lazy(() => import('./pages/TreePage'));
const JarvisPage = lazy(() => import('./pages/JarvisPage'));
const SelfImprovePage = lazy(() => import('./pages/SelfImprovePage'));

/** Activates desktop notification listener for agent failures. */
function DesktopNotifications() {
  useDesktopNotificationListener();
  return null;
}

/** Routes voice commands from FloatingMic to navigation, actions, or Jarvis. */
function VoiceCommandRouter() {
  useVoiceCommands();
  return null;
}

function PageFallback() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="h-8 w-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, refetchOnWindowFocus: true },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ScopeProvider>
        <ToastProvider>
          <NotificationProvider>
          <BrowserRouter>
            <CommandPalette />
            <KeyboardShortcuts />
            <CocoOrb />
            <DesktopNotifications />
            <VoiceCommandRouter />
            <Suspense fallback={<PageFallback />}>
              <Routes>
                <Route element={<AppShell />}>
                  <Route index element={<ErrorBoundary><HomePage /></ErrorBoundary>} />
                  <Route path="analytics" element={<ErrorBoundary><DashboardPage /></ErrorBoundary>} />
                  <Route path="projects" element={<ErrorBoundary><ProjectsPage /></ErrorBoundary>} />
                  <Route path="projects/:projectId" element={<ErrorBoundary><ProjectDetailPage /></ErrorBoundary>} />
                  <Route path="projects/:projectId/:tab" element={<ErrorBoundary><ProjectDetailPage /></ErrorBoundary>} />
                  <Route path="agents" element={<ErrorBoundary><AgentsPage /></ErrorBoundary>} />
                  <Route path="knowledge" element={<ErrorBoundary><KnowledgePage /></ErrorBoundary>} />
                  <Route path="inbox" element={<ErrorBoundary><InboxPage /></ErrorBoundary>} />
                  <Route path="todos" element={<ErrorBoundary><TodosPage /></ErrorBoundary>} />
                  <Route path="goals" element={<ErrorBoundary><GoalsPage /></ErrorBoundary>} />
                  <Route path="chat" element={<ErrorBoundary><ChatPage /></ErrorBoundary>} />
                  <Route path="costs" element={<ErrorBoundary><CostsPage /></ErrorBoundary>} />
                  <Route path="activity" element={<ErrorBoundary><ActivityPage /></ErrorBoundary>} />
                  <Route path="tree" element={<ErrorBoundary><TreePage /></ErrorBoundary>} />
                  <Route path="tree/:nodeId" element={<ErrorBoundary><TreePage /></ErrorBoundary>} />
                  <Route path="self-improve" element={<ErrorBoundary><SelfImprovePage /></ErrorBoundary>} />
                  <Route path="settings" element={<ErrorBoundary><SettingsPage /></ErrorBoundary>} />
                </Route>
                {/* Jarvis renders outside AppShell for full-bleed dark experience */}
                <Route path="jarvis" element={<ErrorBoundary><JarvisPage /></ErrorBoundary>} />
              </Routes>
            </Suspense>
          </BrowserRouter>
          </NotificationProvider>
        </ToastProvider>
      </ScopeProvider>
    </QueryClientProvider>
  );
}
