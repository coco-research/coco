import { useQuery, useQueryClient } from '@tanstack/react-query';
import { FileJson, Trash2, Download, Library } from 'lucide-react';
import { apiFetch, apiDelete } from '../../lib/api';

interface SavedTemplate {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
}

interface TemplateData {
  version: number;
  type: string;
  exported_at: string;
  project: { name: string };
  agents: unknown[];
  goals: unknown[];
  tasks: unknown[];
  todos: unknown[];
}

interface SavedTemplateDetail extends SavedTemplate {
  template: TemplateData;
}

function downloadJson(data: unknown, filename: string) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function TemplateLibrary() {
  const queryClient = useQueryClient();

  const { data: templates, isLoading } = useQuery<SavedTemplate[]>({
    queryKey: ['templates'],
    queryFn: () => apiFetch<SavedTemplate[]>('/templates'),
  });

  const handleDelete = async (id: string) => {
    await apiDelete(`/templates/${id}`);
    queryClient.invalidateQueries({ queryKey: ['templates'] });
  };

  const handleDownload = async (tpl: SavedTemplate) => {
    const detail = await apiFetch<SavedTemplateDetail>(`/templates/${tpl.id}`);
    const safeName = tpl.name.toLowerCase().replace(/[^a-z0-9]+/g, '-');
    downloadJson(detail.template, `${safeName}.coco-template.json`);
  };

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-14 rounded-lg bg-muted/50" />
        ))}
      </div>
    );
  }

  if (!templates || templates.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <Library size={32} className="mx-auto mb-2 opacity-30" />
        <p className="text-sm font-medium">No saved templates</p>
        <p className="text-xs mt-1">Export a project to save it here</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {templates.map((tpl) => (
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
              onClick={() => handleDownload(tpl)}
              className="p-1.5 text-muted-foreground hover:text-foreground transition-colors rounded"
              title="Download as file"
            >
              <Download size={14} />
            </button>
            <button
              onClick={() => handleDelete(tpl.id)}
              className="p-1.5 text-muted-foreground hover:text-destructive transition-colors rounded"
              title="Delete"
            >
              <Trash2 size={14} />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
