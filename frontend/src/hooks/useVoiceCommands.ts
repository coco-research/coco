import { useEffect, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { apiPost } from '../lib/api';
import { useToast } from '../components/shared/Toast';

/**
 * Route map: spoken page names -> paths.
 * Handles common variations ("dashboard", "home", "analytics", etc.)
 */
const PAGE_ROUTES: Record<string, string> = {
  home: '/',
  dashboard: '/',
  analytics: '/analytics',
  projects: '/projects',
  teams: '/projects',
  agents: '/agents',
  agent: '/agents',
  knowledge: '/knowledge',
  inbox: '/inbox',
  decisions: '/inbox',
  todos: '/todos',
  todo: '/todos',
  goals: '/goals',
  chat: '/chat',
  costs: '/costs',
  budget: '/costs',
  activity: '/activity',
  settings: '/settings',
  tree: '/tree',
  portfolio: '/tree',
  jarvis: '/?jarvis=true',
};

interface CommandResponse {
  reply: string;
  action?: string;
  url?: string;
}

/**
 * Global voice command router.
 *
 * Listens for `coco:voice-command` CustomEvents dispatched by FloatingMic
 * and routes them:
 *
 *   - "go to {page}" / "open {page}" / "show {page}" -> navigate()
 *   - "new todo {title}" / "add todo {title}" -> POST /api/todos
 *   - "search {query}" / "find {query}" -> open CommandPalette with query
 *   - "approve" / "reject" -> trigger inbox action if on /inbox
 *   - anything else -> POST /api/jarvis/command, show response as toast
 *
 * Mount this once in App.tsx.
 */
export function useVoiceCommands() {
  const navigate = useNavigate();
  const location = useLocation();
  const { toast } = useToast();

  const handleCommand = useCallback(
    async (text: string) => {
      const lower = text.toLowerCase().trim();

      // ─── Activate Jarvis ────────────────────────────────────────
      if (/^(?:activate\s+jarvis|open\s+jarvis|launch\s+jarvis|jarvis)$/.test(lower)) {
        navigate('/?jarvis=true');
        toast('Activating Jarvis', 'info');
        return;
      }

      // ─── Navigation ─────────────────────────────────────────────
      const navMatch = lower.match(/^(?:go\s+to|open|show|navigate\s+to)\s+(.+)$/);
      if (navMatch) {
        const target = navMatch[1].trim().replace(/\s+/g, '').toLowerCase();
        const path = PAGE_ROUTES[target];
        if (path) {
          navigate(path);
          toast(`Navigating to ${navMatch[1]}`, 'info');
          return;
        }
      }

      // ─── Quick create: new todo ─────────────────────────────────
      const todoMatch = lower.match(/^(?:new|add|create)\s+todo\s+(.+)$/);
      if (todoMatch) {
        const title = todoMatch[1].trim();
        window.dispatchEvent(new CustomEvent('coco:voice-processing'));
        try {
          await apiPost('/todos', { title, priority: 'medium' });
          const reply = `Created todo: "${title}"`;
          toast(reply, 'success');
          window.dispatchEvent(
            new CustomEvent('coco:voice-response', {
              detail: { text: reply, speaking: false },
            })
          );
        } catch {
          toast('Failed to create todo', 'error');
          window.dispatchEvent(
            new CustomEvent('coco:voice-response', {
              detail: { text: 'Failed to create todo.', speaking: false },
            })
          );
        }
        return;
      }

      // ─── Search / Find ──────────────────────────────────────────
      const searchMatch = lower.match(/^(?:search|find|look\s+up|look\s+for)\s+(.+)$/);
      if (searchMatch) {
        // Open CommandPalette by simulating Cmd+K, then setting query
        // The CommandPalette listens for Cmd+K. We dispatch it, then
        // set the query via a custom event.
        const query = searchMatch[1].trim();
        // Trigger the palette open
        window.dispatchEvent(
          new KeyboardEvent('keydown', {
            key: 'k',
            metaKey: true,
            bubbles: true,
          })
        );
        // Small delay then set search text
        setTimeout(() => {
          const input = document.querySelector<HTMLInputElement>(
            '[placeholder="Search pages and actions..."]'
          );
          if (input) {
            // Use native input value setter to trigger React onChange
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
              window.HTMLInputElement.prototype,
              'value'
            )?.set;
            nativeInputValueSetter?.call(input, query);
            input.dispatchEvent(new Event('input', { bubbles: true }));
          }
        }, 150);
        return;
      }

      // ─── Approve / Reject on Inbox ──────────────────────────────
      if (location.pathname === '/inbox') {
        if (lower === 'approve' || lower === 'accept') {
          window.dispatchEvent(
            new CustomEvent('coco:action', { detail: { type: 'inbox-approve' } })
          );
          toast('Approved', 'success');
          return;
        }
        if (lower === 'reject' || lower === 'decline') {
          window.dispatchEvent(
            new CustomEvent('coco:action', { detail: { type: 'inbox-reject' } })
          );
          toast('Rejected', 'info');
          return;
        }
      }

      // ─── Fallback: send to Jarvis command endpoint ──────────────
      window.dispatchEvent(new CustomEvent('coco:voice-processing'));
      try {
        const result = await apiPost<CommandResponse>('/jarvis/command', {
          text,
        });

        // If Jarvis says navigate, do it
        if (result.action === 'navigate' && result.url?.startsWith('/')) {
          navigate(result.url);
        }

        toast(result.reply, 'info');
        window.dispatchEvent(
          new CustomEvent('coco:voice-response', {
            detail: { text: result.reply, speaking: false },
          })
        );
      } catch {
        const fallback = 'Something went wrong. Try again.';
        toast(fallback, 'error');
        window.dispatchEvent(
          new CustomEvent('coco:voice-response', {
            detail: { text: fallback, speaking: false },
          })
        );
      }
    },
    [navigate, location.pathname, toast]
  );

  // Listen for voice command events from FloatingMic
  useEffect(() => {
    function onVoiceCommand(e: Event) {
      const { text } = (e as CustomEvent).detail;
      if (text) handleCommand(text);
    }

    window.addEventListener('coco:voice-command', onVoiceCommand);
    return () => window.removeEventListener('coco:voice-command', onVoiceCommand);
  }, [handleCommand]);
}
