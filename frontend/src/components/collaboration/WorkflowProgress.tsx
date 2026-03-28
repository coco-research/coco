import React from 'react';
import { Check } from 'lucide-react';
import { cn } from '../../lib/utils';
import { ROLE_META } from '../agents/AgentCard';

export interface WorkflowStep {
  role: string;
  action: string;
  section: string;
}

export interface WorkflowProgressProps {
  steps: WorkflowStep[];
  currentStep: number;
  className?: string;
}

function humanize(snake: string): string {
  return snake.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

export const WorkflowProgress = React.memo(function WorkflowProgress({
  steps, currentStep, className,
}: WorkflowProgressProps) {
  return (
    <div className={cn('flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-0', className)}>
      {steps.map((step, i) => {
        const meta = ROLE_META[step.role] ?? ROLE_META['custom'];
        const Icon = meta.icon;
        const completed = i < currentStep;
        const active = i === currentStep;

        return (
          <React.Fragment key={i}>
            {i > 0 && (
              <div className={cn(
                'hidden sm:block w-8 h-0.5 mx-1',
                completed ? 'bg-success' : 'bg-border',
              )} />
            )}
            <div className="flex flex-row sm:flex-col items-center gap-2 sm:gap-1">
              <div className={cn(
                'flex items-center justify-center w-8 h-8 rounded-full border-2 transition-colors',
                completed && 'bg-success/20 border-success text-success',
                active && 'bg-info/20 border-info text-info animate-pulse-dot',
                !completed && !active && 'bg-muted border-border text-muted-foreground',
              )}>
                {completed ? <Check size={14} /> : <Icon size={14} />}
              </div>
              <div className="flex flex-col sm:items-center">
                <span className="text-[10px] font-semibold text-foreground">{meta.abbr}</span>
                <span className="text-[10px] text-muted-foreground">{humanize(step.action)}</span>
              </div>
            </div>
          </React.Fragment>
        );
      })}
    </div>
  );
});
