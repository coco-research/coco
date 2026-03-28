import { useState } from 'react';
import { cn } from '../../../lib/utils';
import { apiPost, apiPatch, apiDelete } from '../../../lib/api';
import { GlassCard } from '../GlassCard';
import { TodoListCard } from './TodoListCard';
import { ProjectDetailCard } from './ProjectDetailCard';
import { HealthDetailCard } from './HealthDetailCard';
import { ApprovalBatchCard } from './ApprovalBatchCard';
import { MetricGridCard } from './MetricGridCard';
import { TextResponseCard } from './TextResponseCard';
import { NavigateHintCard } from './NavigateHintCard';
import type {
  CardData,
  CardAction,
  TodoListData,
  ProjectDetailData,
  HealthDetailData,
  ApprovalBatchData,
  MetricGridData,
  TextResponseData,
  NavigateHintData,
} from '../../../types/cards';

interface ActionCardProps {
  card: CardData;
  variant?: 'jarvis' | 'light';
  delay?: number;
}

function StandardCard({
  children,
  className,
  delay = 0,
}: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}) {
  return (
    <div
      className={cn(
        'jarvis-reveal rounded-xl bg-card border border-border p-4',
        className,
      )}
      style={{ '--reveal-delay': `${delay}ms` } as React.CSSProperties}
    >
      {children}
    </div>
  );
}

function ActionButton({
  action,
  variant,
}: {
  action: CardAction;
  variant: 'jarvis' | 'light';
}) {
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const isJarvis = variant === 'jarvis';

  const handleClick = async () => {
    if (!action.endpoint || loading || done) return;
    setLoading(true);
    try {
      if (action.method === 'PATCH') {
        await apiPatch(action.endpoint, action.payload ?? {});
      } else if (action.method === 'DELETE') {
        await apiDelete(action.endpoint);
      } else {
        await apiPost(action.endpoint, action.payload ?? {});
      }
      setDone(true);
    } catch {
      // Silently fail -- card stays actionable
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={loading || done}
      className={cn(
        'px-3 py-1.5 text-xs font-medium rounded-md transition-all',
        isJarvis
          ? done
            ? 'bg-[#34C759]/15 text-[#34C759] border border-[#34C759]/20'
            : 'bg-[#0A84FF]/10 text-[#0A84FF] border border-white/10 hover:bg-[#0A84FF]/20'
          : done
            ? 'bg-green-100 text-green-700 border border-green-200'
            : 'bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20',
        (loading || done) && 'cursor-default',
      )}
    >
      {done ? 'Done' : loading ? '...' : action.label}
    </button>
  );
}

function CardBody({
  card,
  variant,
  delay,
}: {
  card: CardData;
  variant: 'jarvis' | 'light';
  delay: number;
}) {
  switch (card.type) {
    case 'todo_list':
      return <TodoListCard data={card.data as TodoListData} variant={variant} />;
    case 'project_detail':
      return (
        <ProjectDetailCard
          data={card.data as ProjectDetailData}
          variant={variant}
          delay={delay}
        />
      );
    case 'health_detail':
      return (
        <HealthDetailCard
          data={card.data as HealthDetailData}
          variant={variant}
          delay={delay}
        />
      );
    case 'approval_batch':
      return (
        <ApprovalBatchCard data={card.data as ApprovalBatchData} variant={variant} />
      );
    case 'metric_grid':
      return (
        <MetricGridCard
          data={card.data as MetricGridData}
          variant={variant}
          delay={delay}
        />
      );
    case 'text_response':
      return (
        <TextResponseCard
          data={card.data as TextResponseData}
          variant={variant}
          delay={delay}
        />
      );
    case 'navigate_hint':
      return (
        <NavigateHintCard
          data={card.data as NavigateHintData}
          variant={variant}
          delay={delay}
        />
      );
    default:
      return (
        <p
          className={cn(
            'text-xs italic',
            variant === 'jarvis' ? 'text-white/40' : 'text-muted-foreground',
          )}
        >
          Unknown card type: {card.type}
        </p>
      );
  }
}

export function ActionCard({ card, variant = 'jarvis', delay = 0 }: ActionCardProps) {
  const isJarvis = variant === 'jarvis';
  const Wrapper = isJarvis ? GlassCard : StandardCard;

  return (
    <Wrapper className="p-4" delay={delay}>
      <CardBody card={card} variant={variant} delay={delay} />

      {card.actions && card.actions.length > 0 && (
        <div
          className={cn(
            'flex flex-wrap gap-2 mt-3 pt-3 border-t',
            isJarvis ? 'border-white/10' : 'border-border',
          )}
        >
          {card.actions.map((action, i) => (
            <ActionButton key={i} action={action} variant={variant} />
          ))}
        </div>
      )}
    </Wrapper>
  );
}
