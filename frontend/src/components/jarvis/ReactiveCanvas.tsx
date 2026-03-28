import { cn } from '../../lib/utils';
import type { CardData } from '../../types/cards';
import { ActionCard } from './cards/ActionCard';

interface ReactiveCanvasProps {
  cards: CardData[];
  mode: 'idle' | 'active' | 'transitioning';
  previousCards: CardData[];
}

function gridClass(count: number): string {
  if (count <= 1) return 'max-w-xl mx-auto';
  if (count === 2) return 'grid grid-cols-2 gap-4';
  return 'grid grid-cols-2 lg:grid-cols-3 gap-4';
}

export function ReactiveCanvas({ cards, mode, previousCards }: ReactiveCanvasProps) {
  if (mode === 'idle') return null;

  // During transition out, show previous cards with exit animation
  if (mode === 'transitioning') {
    const displayCards = previousCards.length > 0 ? previousCards : cards;
    return (
      <div className="max-w-5xl mx-auto px-4">
        <div className={cn(gridClass(displayCards.length), 'animate-canvas-exit')}>
          {displayCards.map((c) => (
            <ActionCard key={c.id} card={c} variant="jarvis" />
          ))}
        </div>
      </div>
    );
  }

  // Active — reveal cards with stagger
  return (
    <div className="max-w-5xl mx-auto px-4">
      <div className={gridClass(cards.length)}>
        {cards.map((c, i) => (
          <ActionCard key={c.id} card={c} variant="jarvis" delay={i * 80} />
        ))}
      </div>
    </div>
  );
}
