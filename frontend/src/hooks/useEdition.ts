/**
 * Edition hook — fetches /api/edition once and caches for the session.
 */

interface EditionInfo {
  edition: 'core' | 'studio';
  isStudio: boolean;
  features: string[];
}

let cached: EditionInfo | null = null;
let fetchPromise: Promise<EditionInfo> | null = null;

function fetchEdition(): Promise<EditionInfo> {
  if (cached) return Promise.resolve(cached);
  if (fetchPromise) return fetchPromise;

  fetchPromise = fetch('/api/edition')
    .then((res) => res.json())
    .then((data: { edition: string; features: string[] }) => {
      cached = {
        edition: data.edition as 'core' | 'studio',
        isStudio: data.edition === 'studio',
        features: data.features,
      };
      return cached;
    })
    .catch(() => {
      // Default to core on error
      cached = { edition: 'core', isStudio: false, features: [] };
      return cached;
    });

  return fetchPromise;
}

// Eagerly kick off the fetch on module load
fetchEdition();

import { useState, useEffect } from 'react';

const DEFAULT: EditionInfo = { edition: 'core', isStudio: false, features: [] };

/**
 * Hook returning the current edition info.
 * Fetches once, then returns cached value.
 */
export function useEdition(): EditionInfo {
  const [info, setInfo] = useState<EditionInfo>(cached ?? DEFAULT);

  useEffect(() => {
    if (cached) {
      setInfo(cached);
      return;
    }
    fetchEdition().then(setInfo);
  }, []);

  return info;
}

/**
 * Check whether a given feature name is a Studio-only feature.
 */
export function isStudioFeature(feature: string): boolean {
  const studioFeatures = [
    'jarvis', 'tts', 'stt', 'replay', 'podcast',
    'self_improve', 'analysis', 'coco_orb',
  ];
  return studioFeatures.includes(feature);
}
