import { useState } from 'react';
import * as Tabs from '@radix-ui/react-tabs';
import { cn } from '../lib/utils';
import { GeneralSettings } from '../components/settings/GeneralSettings';
import { AutonomySettings } from '../components/settings/AutonomySettings';
import { DisplaySettings } from '../components/settings/DisplaySettings';
import { BrainViewer } from '../components/settings/BrainViewer';
import { useTheme } from '../context/ThemeContext';
import { Sun, Moon } from 'lucide-react';

type SaveStatus = 'idle' | 'saving' | 'saved';

const tabTriggerCls = cn(
  'px-3 py-2 text-sm font-medium text-muted-foreground transition-colors',
  'hover:text-foreground',
  'data-[state=active]:text-foreground data-[state=active]:border-b-2 data-[state=active]:border-primary',
);

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
          <Tabs.Trigger value="advanced" className={tabTriggerCls}>
            Advanced
          </Tabs.Trigger>
        </Tabs.List>

        <Tabs.Content value="general" className="flex-1 overflow-y-auto py-4 space-y-6">
          <GeneralSettings onSaveStatus={setSaveStatus} />
          <DisplaySettings onSaveStatus={setSaveStatus} />
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
