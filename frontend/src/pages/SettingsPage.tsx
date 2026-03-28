import { useState, useEffect, useCallback } from 'react';
import * as Tabs from '@radix-ui/react-tabs';
import { cn } from '../lib/utils';
import { GeneralSettings } from '../components/settings/GeneralSettings';
import { AutonomySettings } from '../components/settings/AutonomySettings';
import { DisplaySettings } from '../components/settings/DisplaySettings';
import { BrainViewer } from '../components/settings/BrainViewer';
import { useTheme } from '../context/ThemeContext';
import { Sun, Moon, BellOff } from 'lucide-react';
import { TriggerList, type Trigger } from '../components/triggers/TriggerList';
import { TriggerForm } from '../components/triggers/TriggerForm';
import {
  isSupported as notifSupported,
  isPermitted as notifPermitted,
  isEnabled as notifEnabled,
  setEnabled as setNotifEnabled,
  requestPermission,
} from '../lib/desktop-notifications';

type SaveStatus = 'idle' | 'saving' | 'saved';

const tabTriggerCls = cn(
  'px-3 py-2 text-sm font-medium text-muted-foreground transition-colors',
  'hover:text-foreground',
  'data-[state=active]:text-foreground data-[state=active]:border-b-2 data-[state=active]:border-primary',
);

function NotificationToggle() {
  const supported = notifSupported();
  const [enabled, setEnabled] = useState(notifEnabled());
  const [permitted, setPermitted] = useState(notifPermitted());

  // Sync permission state on mount (could change outside our control)
  useEffect(() => {
    setPermitted(notifPermitted());
  }, []);

  const toggle = useCallback(async () => {
    if (!supported) return;

    if (!enabled) {
      // Turning on: request permission first
      const granted = await requestPermission();
      setPermitted(granted);
      if (granted) {
        setNotifEnabled(true);
        setEnabled(true);
      }
    } else {
      // Turning off
      setNotifEnabled(false);
      setEnabled(false);
    }
  }, [enabled, supported]);

  if (!supported) {
    return (
      <div className="flex items-center justify-between py-3 border-b border-border opacity-50">
        <div>
          <p className="text-sm font-medium text-foreground">Desktop Notifications</p>
          <p className="text-xs text-muted-foreground">Not supported in this browser.</p>
        </div>
        <BellOff size={16} className="text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="flex items-center justify-between py-3 border-b border-border">
      <div>
        <p className="text-sm font-medium text-foreground">Desktop Notifications</p>
        <p className="text-xs text-muted-foreground">
          {!permitted && !enabled
            ? 'Get alerts when agents crash or fail. Click to grant permission.'
            : enabled
              ? 'You will receive desktop alerts for agent failures.'
              : 'Enable desktop alerts for agent failures.'}
        </p>
      </div>
      <button
        onClick={toggle}
        className={cn(
          'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
          enabled ? 'bg-accent' : 'bg-border',
        )}
        aria-label={enabled ? 'Disable desktop notifications' : 'Enable desktop notifications'}
      >
        <span
          className={cn(
            'inline-block h-4 w-4 transform rounded-full bg-card transition-transform',
            enabled ? 'translate-x-6' : 'translate-x-1',
          )}
        />
      </button>
    </div>
  );
}

function AutomationsTab() {
  const [editingTrigger, setEditingTrigger] = useState<Trigger | null>(null);

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h3 className="text-sm font-semibold text-foreground mb-1">Triggers</h3>
        <p className="text-xs text-muted-foreground mb-3">
          Automate actions based on schedules, webhooks, or file changes.
        </p>
        <TriggerList onEdit={(t) => setEditingTrigger(t)} />
      </div>
      <div className="border-t border-border pt-4">
        <TriggerForm
          editingTrigger={editingTrigger}
          onDone={() => setEditingTrigger(null)}
        />
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('idle');
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-semibold text-foreground">Settings</h2>
          <p className="text-xs text-muted-foreground mt-0.5">Configure CoCo Platform</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium bg-secondary text-secondary-foreground rounded-md hover:bg-accent/50 transition-colors"
          >
            {theme === 'dark' ? <Sun size={14} /> : <Moon size={14} />}
            {theme === 'dark' ? 'Light' : 'Dark'}
          </button>
          {saveStatus !== 'idle' && (
            <span className={cn(
              'text-xs font-medium px-2 py-1 rounded',
              saveStatus === 'saving' ? 'text-warning' : 'text-success',
            )}>
              {saveStatus === 'saving' ? 'Saving...' : 'Saved \u2713'}
            </span>
          )}
        </div>
      </div>

      <Tabs.Root defaultValue="general" className="flex-1 flex flex-col overflow-hidden">
        <Tabs.List className="flex border-b border-border shrink-0">
          <Tabs.Trigger value="general" className={tabTriggerCls}>
            General
          </Tabs.Trigger>
          <Tabs.Trigger value="automations" className={tabTriggerCls}>
            Automations
          </Tabs.Trigger>
          <Tabs.Trigger value="advanced" className={tabTriggerCls}>
            Advanced
          </Tabs.Trigger>
        </Tabs.List>

        <Tabs.Content value="general" className="flex-1 overflow-y-auto py-4 space-y-6">
          <GeneralSettings onSaveStatus={setSaveStatus} />
          <DisplaySettings onSaveStatus={setSaveStatus} />
          <div className="max-w-lg">
            <NotificationToggle />
          </div>
        </Tabs.Content>

        <Tabs.Content value="automations" className="flex-1 overflow-y-auto py-4">
          <AutomationsTab />
        </Tabs.Content>

        <Tabs.Content value="advanced" className="flex-1 overflow-y-auto py-4 space-y-6">
          <AutonomySettings onSaveStatus={setSaveStatus} />
          <details className="border border-border rounded-lg">
            <summary className="px-4 py-3 text-sm font-medium text-foreground cursor-pointer hover:bg-accent/30 rounded-lg">
              Brain Data (read-only)
            </summary>
            <div className="px-4 pb-4">
              <BrainViewer />
            </div>
          </details>
        </Tabs.Content>
      </Tabs.Root>
    </div>
  );
}
