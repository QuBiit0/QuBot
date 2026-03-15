'use client';

import { useActivityStore, ActivityEvent } from '@/store/activity.store';

export function useActivity() {
  const entries = useActivityStore((s) => s.entries);
  const isPaused = useActivityStore((s) => s.isPaused);
  const filter = useActivityStore((s) => s.filter);
  const addEntry = useActivityStore((s) => s.addEntry);
  const clear = useActivityStore((s) => s.clear);
  const togglePause = useActivityStore((s) => s.togglePause);
  const setFilter = useActivityStore((s) => s.setFilter);
  const getFilteredEntries = useActivityStore((s) => s.getFilteredEntries);
  const getRecentEntries = useActivityStore((s) => s.getRecentEntries);

  return {
    entries,
    isPaused,
    filter,
    addEntry,
    clear,
    togglePause,
    setFilter,
    getFilteredEntries,
    getRecentEntries,
    filteredEntries: getFilteredEntries(),
  };
}

export function useActivityFeed(maxEntries: number = 50) {
  const entries = useActivityStore((s) => s.getRecentEntries(maxEntries));
  const isPaused = useActivityStore((s) => s.isPaused);
  const togglePause = useActivityStore((s) => s.togglePause);
  const clear = useActivityStore((s) => s.clear);

  return {
    entries,
    isPaused,
    togglePause,
    clear,
  };
}
