import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Plus, FolderKanban, Users, Package, Folder, ChevronRight, Upload } from 'lucide-react';
import { apiFetch } from '../lib/api';
import { cn } from '../lib/utils';
import { useScope, type TreeNode } from '../context/ScopeContext';
import { ImportTemplateDialog } from '../components/projects/ImportTemplateDialog';

interface Project {
  id: string;
  name: string;
  jira_key?: string | null;
  confluence_space?: string | null;
  active: number;
  item_count: number;
}

const NODE_ICONS: Record<string, React.ElementType> = {
  group: Folder,
  team: Users,
  product: Package,
  project: FolderKanban,
};

function ProjectsSkeleton() {
  const pulse = 'animate-pulse rounded-xl bg-muted/50';
  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div className={`${pulse} h-8 w-40`} />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className={`${pulse} h-36`} />
        ))}
      </div>
    </div>
  );
}

function NodeCard({ node, project }: { node: TreeNode; project?: Project }) {
  const Icon = NODE_ICONS[node.node_type] ?? FolderKanban;
  const childCount = node.children?.length ?? 0;
  const hasHub = !!node.hub_project_id;

  // All nodes navigate to their detail page.
  // Hub-linked nodes go to /projects/{id}, others go to /node/{id}
  const linkTo = hasHub ? `/projects/${node.hub_project_id}` : `/node/${node.id}`;

  return (
    <Link
      to={linkTo}
      className={cn(
        'rounded-xl border border-border bg-card p-4 hover:shadow-md transition-all block',
        node.color ? 'border-l-4' : 'border-l-4 border-l-border',
      )}
      style={node.color ? { borderLeftColor: node.color } : undefined}
    >
      <NodeCardContent node={node} Icon={Icon} project={project} childCount={childCount} />
      {!hasHub && childCount > 0 && (
        <div className="flex items-center gap-1 mt-2 text-[10px] text-accent">
          <ChevronRight size={10} />
          {childCount} item{childCount !== 1 ? 's' : ''}
        </div>
      )}
    </Link>
  );
}

function NodeCardContent({ node, Icon, project, childCount }: {
  node: TreeNode; Icon: React.ElementType; project?: Project; childCount: number;
}) {
  return (
    <>
      <div className="flex items-center gap-2 mb-2">
        <Icon size={14} className="text-muted-foreground shrink-0" />
        <h3 className="text-sm font-medium text-foreground truncate">{node.label}</h3>
        <span className="ml-auto text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded capitalize">
          {node.node_type}
        </span>
      </div>

      <div className="space-y-1 text-xs text-muted-foreground">
        {project && (
          <div className="flex items-center justify-between">
            <span>Items</span>
            <span className="font-medium text-foreground">{project.item_count}</span>
          </div>
        )}
        {project?.jira_key && (
          <div className="flex items-center justify-between">
            <span>Jira</span>
            <span className="font-mono text-foreground">{project.jira_key}</span>
          </div>
        )}
        {childCount > 0 && !project && (
          <div className="flex items-center justify-between">
            <span>Children</span>
            <span className="font-medium text-foreground">{childCount}</span>
          </div>
        )}
      </div>
    </>
  );
}

function TreeSection({ node, projects }: { node: TreeNode; projects: Map<string, Project> }) {
  const children = node.children ?? [];
  if (children.length === 0 && !node.hub_project_id) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        {node.color && (
          <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: node.color }} />
        )}
        <h2 className="text-sm font-semibold text-foreground">{node.label}</h2>
        <span className="text-xs text-muted-foreground">({children.length})</span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {children.map(child => (
          <NodeCard
            key={child.id}
            node={child}
            project={child.hub_project_id ? projects.get(child.hub_project_id) : undefined}
          />
        ))}
      </div>
    </div>
  );
}

export default function ProjectsPage() {
  const { tree, loading: treeLoading } = useScope();
  const [importOpen, setImportOpen] = useState(false);

  const { data: projectList, isLoading: projectsLoading } = useQuery<Project[]>({
    queryKey: ['projects'],
    queryFn: () => apiFetch<Project[]>('/projects'),
  });

  if (treeLoading || projectsLoading) return <ProjectsSkeleton />;

  // Build project lookup
  const projectMap = new Map<string, Project>();
  for (const p of projectList ?? []) {
    projectMap.set(p.id, p);
  }

  // Get top-level groups from tree
  const topNodes = tree?.children ?? [];

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Teams</h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            {projectList?.length ?? 0} stakeholder teams across {topNodes.length} groups
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setImportOpen(true)}
            className="inline-flex items-center gap-2 rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground hover:bg-accent/30 transition-all"
          >
            <Upload size={14} />
            Import Template
          </button>
          <Link
            to="/tree"
            className="inline-flex items-center gap-2 rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground hover:bg-accent/30 transition-all"
          >
            Manage Tree
            <ChevronRight size={14} />
          </Link>
        </div>
      </div>

      {topNodes.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
          <FolderKanban size={40} className="mb-3 opacity-30" />
          <p className="text-sm font-medium">No groups yet</p>
          <p className="text-xs mt-1">
            Go to <Link to="/tree" className="text-accent hover:underline">My Portfolio</Link> to build your hierarchy.
          </p>
        </div>
      ) : (
        topNodes.map(group => (
          <TreeSection key={group.id} node={group} projects={projectMap} />
        ))
      )}

      <ImportTemplateDialog
        open={importOpen}
        onOpenChange={setImportOpen}
        onImported={() => {
          // Refresh tree and projects after import
        }}
      />
    </div>
  );
}
