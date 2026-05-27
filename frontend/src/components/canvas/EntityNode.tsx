import { memo } from 'react';
import { Handle, Position, type Node, type NodeProps } from '@xyflow/react';
import { User, Users, Monitor, FileText, Briefcase, Box, Building2, Waypoints } from 'lucide-react';
import { cn } from '../../lib/utils';

export type EntityNodeData = {
  label: string;
  entityType: string;
  gid: string;
  articleCount: number;
  confidence: number;
  [key: string]: unknown;
};

export type EntityNodeT = Node<EntityNodeData, 'entity'>;

const TYPE_COLORS: Record<string, string> = {
  person: 'bg-blue-950/80 border-blue-700/60',
  team: 'bg-purple-950/80 border-purple-700/60',
  system: 'bg-green-950/80 border-green-700/60',
  document: 'bg-amber-950/80 border-amber-700/60',
  role: 'bg-pink-950/80 border-pink-700/60',
  org_unit: 'bg-teal-950/80 border-teal-700/60',
  module: 'bg-indigo-950/80 border-indigo-700/60',
  project: 'bg-cyan-950/80 border-cyan-700/60',
};

const TYPE_ICONS: Record<string, React.ElementType> = {
  person: User,
  team: Users,
  system: Monitor,
  document: FileText,
  role: Briefcase,
  org_unit: Building2,
  module: Box,
  project: Waypoints,
};

function EntityNodeComponent({ data, selected }: NodeProps<EntityNodeT>) {
  const nodeData = data;
  const Icon = TYPE_ICONS[nodeData.entityType] ?? Box;
  const colors = TYPE_COLORS[nodeData.entityType] ?? 'bg-gray-900/80 border-gray-600/60';

  return (
    <div
      className={cn(
        'px-3 py-2 rounded-lg border shadow-md min-w-[130px] max-w-[200px] backdrop-blur-sm transition-all',
        colors,
        selected ? 'ring-2 ring-accent border-accent shadow-accent/20' : '',
      )}
    >
      <Handle type="target" position={Position.Top} className="!bg-accent !w-2 !h-2 !border-0" />
      <div className="flex items-center gap-1.5">
        <Icon size={12} className="text-muted-foreground shrink-0" />
        <span className="text-xs font-medium text-foreground truncate">{nodeData.label}</span>
      </div>
      <div className="flex items-center gap-1.5 mt-1">
        <span className="text-[10px] text-muted-foreground capitalize">{nodeData.entityType}</span>
        {nodeData.articleCount > 0 && (
          <span className="text-[10px] bg-accent/20 text-accent px-1 rounded font-medium">
            {nodeData.articleCount}
          </span>
        )}
        {nodeData.confidence > 0 && (
          <span className="text-[10px] text-muted-foreground/60 ml-auto">
            {Math.round(nodeData.confidence * 100)}%
          </span>
        )}
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-accent !w-2 !h-2 !border-0" />
    </div>
  );
}

export const EntityNode = memo(EntityNodeComponent);
