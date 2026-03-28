import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { apiPost, apiPatch, apiDelete } from '../lib/api';
import type { CardAction } from '../types/cards';

export function useCardActions() {
  const qc = useQueryClient();
  const [loadingAction, setLoadingAction] = useState<string | null>(null);

  const execute = async (action: CardAction) => {
    if (!action.endpoint) return;
    setLoadingAction(action.action);
    try {
      if (action.method === 'PATCH') {
        await apiPatch(action.endpoint, action.payload ?? {});
      } else if (action.method === 'DELETE') {
        await apiDelete(action.endpoint);
      } else {
        await apiPost(action.endpoint, action.payload ?? {});
      }
      qc.invalidateQueries({ queryKey: ['todos'] });
      qc.invalidateQueries({ queryKey: ['home'] });
      qc.invalidateQueries({ queryKey: ['drafts'] });
    } finally {
      setLoadingAction(null);
    }
  };

  return { execute, loadingAction };
}
