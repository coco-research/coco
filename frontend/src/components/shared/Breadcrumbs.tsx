import { useMemo } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import { useScope, type TreeNode } from '../../context/ScopeContext';

const PAGE_LABELS: Record<string, string> = {
  projects: 'Teams',
  tree: 'My Portfolio',
  agents: 'Agent Team',
  knowledge: 'Knowledge',
  inbox: 'Inbox',
  todos: 'Todos',
  goals: 'Goals',
  chat: 'Chat',
  costs: 'Costs & Budget',
  activity: 'Activity',
  settings: 'Settings',
};

function buildNodeMap(root: TreeNode | null): Map<string, TreeNode> {
  const map = new Map<string, TreeNode>();
  if (!root) return map;
  const walk = (n: TreeNode) => { map.set(n.id, n); n.children?.forEach(walk); };
  walk(root);
  return map;
}

export function Breadcrumbs() {
  const { pathname } = useLocation();
  const { tree } = useScope();

  const segments = pathname.split('/').filter(Boolean);
  const nodeMap = useMemo(() => buildNodeMap(tree), [tree]);

  // ── Tree routes: /tree and /tree/:nodeId ──
  if (segments[0] === 'tree') {
    const nodeId = segments[1];
    if (!nodeId) {
      return <span className="text-sm font-semibold text-foreground">My Portfolio</span>;
    }

    const node = nodeMap.get(nodeId);
    const crumbs: { label: string; to?: string }[] = [{ label: 'My Portfolio', to: '/tree' }];

    if (node) {
      const pathIds = node.path.split('/').filter(Boolean);
      pathIds.pop(); // remove self
      for (const id of pathIds) {
        const ancestor = nodeMap.get(id);
        if (ancestor) crumbs.push({ label: ancestor.label, to: `/tree/${id}` });
      }
      crumbs.push({ label: node.label });
    } else {
      crumbs.push({ label: nodeId }); // fallback while loading
    }

    return <CrumbNav crumbs={crumbs} />;
  }

  // ── All other routes ──
  if (segments.length === 0) {
    return <span className="text-sm font-semibold text-foreground">Home</span>;
  }

  const crumbs: { label: string; to?: string }[] = [];
  for (let i = 0; i < segments.length; i++) {
    const seg = segments[i];
    const path = '/' + segments.slice(0, i + 1).join('/');
    const isLast = i === segments.length - 1;

    if (i === 0) {
      crumbs.push({ label: PAGE_LABELS[seg] || capitalize(seg), to: isLast ? undefined : path });
    } else if (segments[0] === 'projects' && i === 1) {
      // seg is a hub_project_id like "demand-892", not a tree node UUID
      let label = seg;
      for (const [, n] of nodeMap) {
        if (n.hub_project_id === seg) { label = n.label; break; }
      }
      crumbs.push({ label, to: isLast ? undefined : path });
    } else {
      crumbs.push({ label: capitalize(seg) });
    }
  }

  return <CrumbNav crumbs={crumbs} />;
}

function CrumbNav({ crumbs }: { crumbs: { label: string; to?: string }[] }) {
  return (
    <nav className="flex items-center gap-1 text-xs text-muted-foreground">
      {crumbs.map((crumb, i) => (
        <span key={i} className="flex items-center gap-1">
          {i > 0 && <ChevronRight size={12} className="text-muted-foreground/50" />}
          {crumb.to ? (
            <Link to={crumb.to} className="hover:text-foreground transition-colors">
              {crumb.label}
            </Link>
          ) : (
            <span className="text-foreground font-semibold">{crumb.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}

function capitalize(s: string) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}
