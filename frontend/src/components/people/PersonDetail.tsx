import { useState } from 'react';
import { X, Trash2, Pencil } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { cn, timeAgo } from '../../lib/utils';
import { apiPatch } from '../../lib/api';
import type { Person } from './PersonCard';

const ROLE_COLORS: Record<string, string> = {
  self: 'bg-accent/20 text-accent',
  manager: 'bg-destructive/20 text-destructive',
  collaborator: 'bg-info/20 text-info',
  stakeholder: 'bg-warning/20 text-warning',
  external: 'bg-accent/50 text-muted-foreground',
};

const PRIORITY_DOT: Record<string, string> = {
  high: 'bg-destructive',
  normal: 'bg-warning',
  low: 'bg-border-strong',
};

interface PersonDetailProps {
  slug: string;
  person: Person;
  onClose: () => void;
}

export function PersonDetail({ slug, person, onClose }: PersonDetailProps) {
  const qc = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [saving, setSaving] = useState(false);

  const [editName, setEditName] = useState(person.full_name);
  const [editRole, setEditRole] = useState<string>(person.role);
  const [editPriority, setEditPriority] = useState<string>(person.priority);
  const [editProjects, setEditProjects] = useState(person.projects.join(', '));
  const emailList = person.patterns.email_from ?? person.patterns.email_patterns ?? [];
  const [editEmails, setEditEmails] = useState(
    emailList.join(', '),
  );

  async function handleSave() {
    setSaving(true);
    try {
      await apiPatch('/brain/people/' + slug, {
        full_name: editName,
        role: editRole,
        priority: editPriority,
        projects: editProjects.split(',').map((s) => s.trim()).filter(Boolean),
        patterns: {
          ...person.patterns,
          email_from: editEmails.split(',').map((s) => s.trim()).filter(Boolean),
        },
      });
      void qc.invalidateQueries({ queryKey: ['people'] });
      setEditing(false);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    setSaving(true);
    try {
      await apiPatch('/brain/people/' + slug + '/delete', {});
      void qc.invalidateQueries({ queryKey: ['people'] });
      onClose();
    } finally {
      setSaving(false);
    }
  }

  const patterns = person.patterns;
  const observationCounts = patterns.observation_counts ?? {};

  return (
    <>
      <div className="fixed inset-0 bg-black/40 z-40" onClick={onClose} />

      <div className="fixed right-0 top-0 h-full w-[500px] max-w-full bg-card border-l border-border shadow-2xl z-50 flex flex-col animate-slide-in">
        {/* Header */}
        <div className="flex items-start gap-3 p-5 border-b border-border">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className={cn('h-2.5 w-2.5 rounded-full', PRIORITY_DOT[person.priority] ?? 'bg-border')} />
              <h2 className="text-lg font-semibold text-foreground truncate">{person.full_name}</h2>
            </div>
            <div className="flex items-center gap-2 mt-1">
              <span
                className={cn(
                  'rounded-full px-2 py-0.5 text-xs font-medium capitalize',
                  ROLE_COLORS[person.role] ?? 'bg-border/30 text-muted-foreground',
                )}
              >
                {person.role}
              </span>
              <span className="text-xs text-muted-foreground">Learned {timeAgo(person.learned_at)}</span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-accent/50 text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {!editing ? (
            <>
              {/* Projects */}
              <Section label="Projects">
                {person.projects.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {person.projects.map((p) => (
                      <span
                        key={p}
                        className="inline-flex items-center rounded bg-accent/20 text-accent px-2 py-0.5 text-xs font-medium"
                      >
                        {p}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span className="text-muted-foreground text-sm italic">None</span>
                )}
              </Section>

              {/* Email Patterns */}
              {((patterns.email_from ?? patterns.email_patterns) ?? []).length > 0 && (
                <Section label="Email Patterns">
                  <ul className="space-y-1">
                    {(patterns.email_from ?? patterns.email_patterns ?? []).map((e, i) => (
                      <li key={i} className="text-sm text-foreground font-mono">{String(e)}</li>
                    ))}
                  </ul>
                </Section>
              )}

              {/* Transcription Aliases */}
              {(patterns.transcription_aliases ?? []).length > 0 && (
                <Section label="Transcription Aliases">
                  <div className="flex flex-wrap gap-1.5">
                    {patterns.transcription_aliases!.map((a, i) => (
                      <span
                        key={i}
                        className="inline-flex items-center rounded bg-warning/20 text-warning px-2 py-0.5 text-xs"
                      >
                        {a}
                      </span>
                    ))}
                  </div>
                </Section>
              )}

              {/* Typical Topics */}
              {(patterns.typical_topics ?? []).length > 0 && (
                <Section label="Typical Topics">
                  <div className="flex flex-wrap gap-1.5">
                    {patterns.typical_topics!.map((t, i) => (
                      <span
                        key={i}
                        className="inline-flex items-center rounded bg-accent/50 px-2 py-0.5 text-xs text-foreground"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                </Section>
              )}

              {/* Communication Frequency */}
              {(patterns.frequency || patterns.communication_frequency) && (
                <Section label="Communication Frequency">
                  <span className="text-sm text-foreground capitalize">{patterns.frequency ?? patterns.communication_frequency}</span>
                </Section>
              )}

              {/* Observation Counts */}
              {Object.keys(observationCounts).length > 0 && (
                <Section label="Observation Counts">
                  <div className="space-y-1.5">
                    {Object.entries(observationCounts).map(([proj, count]) => (
                      <div key={proj} className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">{proj}</span>
                        <span className="text-foreground font-medium">{count}</span>
                      </div>
                    ))}
                  </div>
                </Section>
              )}

              {/* Source */}
              <Section label="Source">
                <span className="text-sm text-foreground capitalize">{person.source}</span>
              </Section>
            </>
          ) : (
            /* Edit form */
            <div className="space-y-4">
              <Field label="Name">
                <input
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="w-full bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors"
                />
              </Field>
              <Field label="Role">
                <select
                  value={editRole}
                  onChange={(e) => setEditRole(e.target.value as string)}
                  className="w-full bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors"
                >
                  <option value="self">Self</option>
                  <option value="manager">Manager</option>
                  <option value="collaborator">Collaborator</option>
                  <option value="stakeholder">Stakeholder</option>
                  <option value="external">External</option>
                </select>
              </Field>
              <Field label="Priority">
                <select
                  value={editPriority}
                  onChange={(e) => setEditPriority(e.target.value as string)}
                  className="w-full bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors"
                >
                  <option value="high">High</option>
                  <option value="normal">Normal</option>
                  <option value="low">Low</option>
                </select>
              </Field>
              <Field label="Projects (comma-separated)">
                <input
                  value={editProjects}
                  onChange={(e) => setEditProjects(e.target.value)}
                  className="w-full bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors"
                />
              </Field>
              <Field label="Email Patterns (comma-separated)">
                <input
                  value={editEmails}
                  onChange={(e) => setEditEmails(e.target.value)}
                  className="w-full bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors"
                />
              </Field>

              <div className="flex gap-2 pt-2">
                <button
                  onClick={() => void handleSave()}
                  disabled={saving}
                  className={cn(
                    'px-4 py-1.5 text-sm rounded-md bg-accent text-accent-foreground hover:bg-accent/80 shadow-sm transition-colors',
                    saving && 'opacity-50',
                  )}
                >
                  Save
                </button>
                <button
                  onClick={() => setEditing(false)}
                  className="px-4 py-1.5 text-sm rounded-md text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer actions */}
        {!editing && (
          <div className="flex items-center gap-2 p-4 border-t border-border">
            <button
              onClick={() => setEditing(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md bg-accent text-accent-foreground hover:bg-accent/80 shadow-sm transition-colors"
            >
              <Pencil className="h-3.5 w-3.5" />
              Edit
            </button>

            {!confirmDelete ? (
              <button
                onClick={() => setConfirmDelete(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md bg-destructive/20 text-destructive hover:bg-destructive/20 transition-colors"
              >
                <Trash2 className="h-3.5 w-3.5" />
                Delete
              </button>
            ) : (
              <div className="flex items-center gap-1.5">
                <span className="text-xs text-destructive">Confirm?</span>
                <button
                  onClick={() => void handleDelete()}
                  disabled={saving}
                  className="px-3 py-1.5 text-sm rounded-md bg-destructive text-white hover:bg-destructive/80 transition-colors"
                >
                  Yes, delete
                </button>
                <button
                  onClick={() => setConfirmDelete(false)}
                  className="px-3 py-1.5 text-sm rounded-md text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors"
                >
                  Cancel
                </button>
              </div>
            )}

            <div className="flex-1" />
            <button
              onClick={onClose}
              className="px-3 py-1.5 text-sm rounded-md text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors"
            >
              Close
            </button>
          </div>
        )}
      </div>
    </>
  );
}

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5">{label}</h3>
      {children}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs font-medium text-muted-foreground mb-1">{label}</label>
      {children}
    </div>
  );
}
