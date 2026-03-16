/**
 * Unit tests for activity store
 */
import { useActivityStore } from '@/store/activity.store';
import type { ActivityEvent } from '@/store/activity.store';

const makeEntry = (overrides: Partial<ActivityEvent> = {}): ActivityEvent => ({
  id: Math.random().toString(36).slice(2),
  timestamp: new Date().toISOString(),
  type: 'test',
  message: 'Test message',
  severity: 'info',
  ...overrides,
});

describe('useActivityStore', () => {
  beforeEach(() => {
    useActivityStore.setState({ entries: [], isPaused: false, filter: 'all' });
  });

  describe('addEntry', () => {
    it('adds an entry to the front of the list', () => {
      const entry = makeEntry({ message: 'hello' });
      useActivityStore.getState().addEntry(entry);
      expect(useActivityStore.getState().entries[0]).toEqual(entry);
    });

    it('does not add when paused', () => {
      useActivityStore.setState({ isPaused: true });
      useActivityStore.getState().addEntry(makeEntry());
      expect(useActivityStore.getState().entries).toHaveLength(0);
    });

    it('caps entries at 200', () => {
      const entries = Array.from({ length: 210 }, () => makeEntry());
      entries.forEach((e) => useActivityStore.getState().addEntry(e));
      expect(useActivityStore.getState().entries).toHaveLength(200);
    });

    it('most recent entry is at index 0', () => {
      const first = makeEntry({ message: 'first' });
      const second = makeEntry({ message: 'second' });
      useActivityStore.getState().addEntry(first);
      useActivityStore.getState().addEntry(second);
      expect(useActivityStore.getState().entries[0].message).toBe('second');
    });
  });

  describe('togglePause', () => {
    it('toggles isPaused', () => {
      expect(useActivityStore.getState().isPaused).toBe(false);
      useActivityStore.getState().togglePause();
      expect(useActivityStore.getState().isPaused).toBe(true);
      useActivityStore.getState().togglePause();
      expect(useActivityStore.getState().isPaused).toBe(false);
    });
  });

  describe('clear', () => {
    it('removes all entries', () => {
      useActivityStore.getState().addEntry(makeEntry());
      useActivityStore.getState().addEntry(makeEntry());
      useActivityStore.getState().clear();
      expect(useActivityStore.getState().entries).toHaveLength(0);
    });
  });

  describe('setFilter', () => {
    it('updates the filter', () => {
      useActivityStore.getState().setFilter('error');
      expect(useActivityStore.getState().filter).toBe('error');
    });
  });

  describe('getFilteredEntries', () => {
    beforeEach(() => {
      useActivityStore.getState().addEntry(makeEntry({ severity: 'info' }));
      useActivityStore.getState().addEntry(makeEntry({ severity: 'error' }));
      useActivityStore.getState().addEntry(makeEntry({ severity: 'warning' }));
    });

    it('returns all entries when filter is "all"', () => {
      expect(useActivityStore.getState().getFilteredEntries()).toHaveLength(3);
    });

    it('filters by severity', () => {
      useActivityStore.getState().setFilter('error');
      const filtered = useActivityStore.getState().getFilteredEntries();
      expect(filtered).toHaveLength(1);
      expect(filtered[0].severity).toBe('error');
    });
  });

  describe('getRecentEntries', () => {
    it('returns the N most recent entries', () => {
      for (let i = 0; i < 10; i++) {
        useActivityStore.getState().addEntry(makeEntry({ message: `msg-${i}` }));
      }
      expect(useActivityStore.getState().getRecentEntries(5)).toHaveLength(5);
    });
  });
});
