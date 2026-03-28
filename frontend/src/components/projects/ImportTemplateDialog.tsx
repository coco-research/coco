import { useState, useRef, useCallback } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { X, Upload, FileJson, Library, Trash2, Eye, ChevronRight } from 'lucide-react';
import { apiFetch, apiPost, apiDelete } from '../../lib/api';
import { cn } from '../../lib/utils';

// ── Types ───────────────────────────────────────────────────────────

interface TemplateProject {
  name: string;
  jira_key?: string | null;
  confluence_space?: string | null;
}

interface TemplateData {
  version: number;
  type: string;
  exported_at: string;
  project: TemplateProject;
  agents: Array<{ name: string; role: string; model: string }>;
  goals: Array<{ title: string }>;
  tasks: Array<{ title: string; priority: string }>;
  todos: Array<{ title: string }>;
  node: Record<string, unknown> | null;
  child_nodes: Array<{ label: string; node_type: string }>;
}

interface SavedTemplate {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
}

interface SavedTemplateDetail extends SavedTemplate {
  template: TemplateData;
}

interface ImportResult {
  node_id: string;
  project_name: string;
  agents_created: number;
  goals_created: number;
  tasks_created: number;
  child_nodes_created: number;
}

interface ImportTemplateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onImported: (result: ImportResult) => void;
  parentNodeId?: string;
}

// ── Styles ──────────────────────────────────────────────────────────

const inputCls =
  'w-full bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors';

const btnPrimary =
  'px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:opacity-90 disabled:opacity-50 transition-opacity';

const btnSecondary =
  'px-4 py-2 text-sm font-medium bg-secondary text-secondary-foreground rounded-md hover:bg-accent/30 transition-colors';

// ── Template Preview ────────────────────────────────────────────────

function TemplatePreview({ template }: { template: TemplateData }) {
  return (
    <div className="space-y-3 text-sm">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <span className="text-xs text-muted-foreground block">Project Name</span>
          <span className="font-medium text-foreground">{template.project.name}</span>
        </div>
        <div>
          <span className="text-xs text-muted-foreground block">Version</span>
          <span className="font-mono text-foreground">v{template.version}</span>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {[
          { label: 'Agents', count: template.agents?.length ?? 0 },
          { label: 'Goals', count: template.goals?.length ?? 0 },
          { label: 'Tasks', count: template.tasks?.length ?? 0 },
          { label: 'Todos', count: template.todos?.length ?? 0 },
        ].map((s) => (
          <div
            key={s.label}
            className="bg-muted/30 rounded-lg px-3 py-2 text-center"
          >
            <span className="text-lg font-semibold text-foreground tabular-nums">{s.count}</span>
            <span className="text-[10px] text-muted-foreground block uppercase tracking-wider">
              {s.label}
            </span>
          </div>
        ))}
      </div>

      {(template.agents?.length ?? 0) > 0 && (
        <div>
          <span className="text-xs text-muted-foreground block mb-1">Agents</span>
          <div className="flex flex-wrap gap-1.5">
            {template.agents.map((a, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-1 text-xs bg-accent/10 text-accent-foreground px-2 py-0.5 rounded"
              >
                {a.name}
                <span className="text-muted-foreground">({a.role})</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {(template.child_nodes?.length ?? 0) > 0 && (
        <div>
          <span className="text-xs text-muted-foreground block mb-1">Child Nodes</span>
          <div className="flex flex-wrap gap-1.5">
            {template.child_nodes.map((n, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-1 text-xs bg-muted/50 text-foreground px-2 py-0.5 rounded"
              >
                {n.label}
                <span className="text-muted-foreground capitalize">({n.node_type})</span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main Dialog ─────────────────────────────────────────────────────

export function ImportTemplateDialog({
  open,
  onOpenChange,
  onImported,
  parentNodeId = 'root',
}: ImportTemplateDialogProps) {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [tab, setTab] = useState<'file' | 'library'>('file');
  const [template, setTemplate] = useState<TemplateData | null>(null);
  const [projectName, setProjectName] = useState('');
  const [fileName, setFileName] = useState('');
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState('');
  const [previewId, setPreviewId] = useState<string | null>(null);

  // Fetch saved templates
  const { data: savedTemplates } = useQuery<SavedTemplate[]>({
    queryKey: ['templates'],
    queryFn: () => apiFetch<SavedTemplate[]>('/templates'),
    enabled: open,
  });

  // Fetch detail for preview
  const { data: previewDetail } = useQuery<SavedTemplateDetail>({
    queryKey: ['templates', previewId],
    queryFn: () => apiFetch<SavedTemplateDetail>(`/templates/${previewId}`),
    enabled: !!previewId,
  });

  const reset = useCallback(() => {
    setTemplate(null);
    setProjectName('');
    setFileName('');
    setError('');
    setPreviewId(null);
    setTab('file');
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileName(file.name);
    setError('');

    const reader = new FileReader();
    reader.onload = () => {
      try {
        const parsed = JSON.parse(reader.result as string);
        if (parsed.type !== 'coco-project-template') {
          setError('Invalid template file: wrong type');
          return;
        }
        setTemplate(parsed);
        setProjectName(parsed.project?.name ?? '');
      } catch {
        setError('Invalid JSON file');
      }
    };
    reader.readAsText(file);
  };

  const handleSelectSaved = (tpl: SavedTemplateDetail) => {
    setTemplate(tpl.template);
    setProjectName(tpl.template.project?.name ?? '');
    setPreviewId(null);
    setTab('file'); // Switch to preview/import mode
  };

  const handleDeleteTemplate = async (id: string) => {
    try {
      await apiDelete(`/templates/${id}`);
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      if (previewId === id) setPreviewId(null);
    } catch {
      // ignore
    }
  };

  const handleImport = async () => {
    if (!template) return;
    setImporting(true);
    setError('');

    try {
      const result = await apiPost<ImportResult>('/projects/import', {
        template,
        parent_node_id: parentNodeId,
        project_name: projectName.trim() || undefined,
      });
      onImported(result);
      reset();
      onOpenChange(false);
      queryClient.invalidateQueries({ queryKey: ['tree'] });
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Import failed');
    } finally {
      setImporting(false);
    }
  };

  return (
    <Dialog.Root
      open={open}
      onOpenChange={(v) => {
        if (!v) reset();
        onOpenChange(v);
      }}
    >
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/40 z-50" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-[560px] max-h-[85vh] overflow-y-auto rounded-xl border border-border bg-popover p-6 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <Dialog.Title className="text-base font-semibold text-foreground">
              Import Template
            </Dialog.Title>
            <Dialog.Close asChild>
              <button className="text-muted-foreground hover:text-foreground transition-colors">
                <X size={16} />
              </button>
            </Dialog.Close>
          </div>

          {/* Tab switcher */}
          {!template && (
            <div className="flex border-b border-border mb-4">
              <button
                onClick={() => setTab('file')}
                className={cn(
                  'px-3 py-2 text-sm font-medium transition-colors',
                  tab === 'file'
                    ? 'text-foreground border-b-2 border-primary'
                    : 'text-muted-foreground hover:text-foreground',
                )}
              >
                <Upload size={14} className="inline mr-1.5 -mt-0.5" />
                From File
              </button>
              <button
                onClick={() => setTab('library')}
                className={cn(
                  'px-3 py-2 text-sm font-medium transition-colors',
                  tab === 'library'
                    ? 'text-foreground border-b-2 border-primary'
                    : 'text-muted-foreground hover:text-foreground',
                )}
              >
                <Library size={14} className="inline mr-1.5 -mt-0.5" />
                Template Library
                {(savedTemplates?.length ?? 0) > 0 && (
                  <span className="ml-1.5 text-xs bg-muted px-1.5 py-0.5 rounded">
                    {savedTemplates!.length}
                  </span>
                )}
              </button>
            </div>
          )}

          {/* File upload tab */}
          {tab === 'file' && !template && (
            <div className="space-y-4">
              <input
                ref={fileInputRef}
                type="file"
                accept=".json,.coco-template.json"
                className="hidden"
                onChange={handleFileChange}
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="w-full border-2 border-dashed border-border rounded-xl p-8 flex flex-col items-center gap-2 hover:border-accent/50 hover:bg-accent/5 transition-all"
              >
                <FileJson size={32} className="text-muted-foreground" />
                <span className="text-sm font-medium text-foreground">
                  {fileName || 'Choose a .coco-template.json file'}
                </span>
                <span className="text-xs text-muted-foreground">
                  Click to browse or drag and drop
                </span>
              </button>
            </div>
          )}

          {/* Library tab */}
          {tab === 'library' && !template && (
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {(!savedTemplates || savedTemplates.length === 0) ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Library size={32} className="mx-auto mb-2 opacity-30" />
                  <p className="text-sm">No saved templates</p>
                  <p className="text-xs mt-1">Export a project to save it as a template</p>
                </div>
              ) : (
                savedTemplates.map((tpl) => (
                  <div
                    key={tpl.id}
                    className="flex items-center gap-3 border border-border rounded-lg p-3 hover:bg-accent/5 transition-colors"
                  >
                    <FileJson size={20} className="text-muted-foreground shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-foreground truncate">{tpl.name}</p>
                      {tpl.description && (
                        <p className="text-xs text-muted-foreground truncate">{tpl.description}</p>
                      )}
                      <p className="text-[10px] text-muted-foreground">
                        {new Date(tpl.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      <button
                        onClick={() => setPreviewId(previewId === tpl.id ? null : tpl.id)}
                        className="p-1.5 text-muted-foreground hover:text-foreground transition-colors rounded"
                        title="Preview"
                      >
                        <Eye size={14} />
                      </button>
                      <button
                        onClick={() => handleDeleteTemplate(tpl.id)}
                        className="p-1.5 text-muted-foreground hover:text-destructive transition-colors rounded"
                        title="Delete"
                      >
                        <Trash2 size={14} />
                      </button>
                      <button
                        onClick={() => {
                          if (previewDetail && previewDetail.id === tpl.id) {
                            handleSelectSaved(previewDetail);
                          } else {
                            // Fetch then select
                            apiFetch<SavedTemplateDetail>(`/templates/${tpl.id}`).then(handleSelectSaved);
                          }
                        }}
                        className="p-1.5 text-accent hover:text-accent/80 transition-colors rounded"
                        title="Use this template"
                      >
                        <ChevronRight size={14} />
                      </button>
                    </div>

                    {/* Inline preview */}
                    {previewId === tpl.id && previewDetail && (
                      <div className="w-full mt-2 pt-2 border-t border-border">
                        <TemplatePreview template={previewDetail.template} />
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          )}

          {/* Template loaded — preview + confirm */}
          {template && (
            <div className="space-y-4">
              <TemplatePreview template={template} />

              <div>
                <label className="text-xs text-muted-foreground block mb-1">Project Name (override)</label>
                <input
                  type="text"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder={template.project.name}
                  className={inputCls}
                />
              </div>

              {error && (
                <p className="text-xs text-destructive">{error}</p>
              )}

              <div className="flex items-center gap-3 justify-end">
                <button
                  onClick={() => {
                    setTemplate(null);
                    setFileName('');
                  }}
                  className={btnSecondary}
                >
                  Back
                </button>
                <button
                  onClick={handleImport}
                  disabled={importing}
                  className={btnPrimary}
                >
                  {importing ? 'Importing...' : 'Import Project'}
                </button>
              </div>
            </div>
          )}

          {/* Error display */}
          {error && !template && (
            <p className="text-xs text-destructive mt-3">{error}</p>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
