import { useCallback, useEffect, useRef, useState } from 'react';
import { INITIAL_PROJECT } from '../initialData';
import { Participant, TournamentProject } from '../types';
import { soundFX } from '../utils/audio';
import { rivalOf } from '../utils/bracketLogic';

const STORAGE_KEY = 'tournament_maker_saved_project';

export function useTournamentProject() {
  const [project, setProject] = useState<TournamentProject>(() => {
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved) {
          const parsed = JSON.parse(saved);
          if (parsed && parsed.slots) return parsed;
        }
      } catch {}
    }
    return INITIAL_PROJECT;
  });

  const [versus, setVersus] = useState<{
    isOpen: boolean;
    tab: number;
    matchIdx: number;
    lastAction?: any;
  }>({
    isOpen: false,
    tab: 0,
    matchIdx: 0,
  });

  const [isConnected, setIsConnected] = useState<boolean>(false);
  const bcRef = useRef<BroadcastChannel | null>(null);

  // Sync to localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(project));
      } catch {}
    }
  }, [project]);

  // Tab-to-tab BroadcastChannel (works for local OBS & multiple tabs without backend)
  useEffect(() => {
    try {
      const bc = new BroadcastChannel('tournament_maker_channel');
      bcRef.current = bc;
      bc.onmessage = (event) => {
        if (event.data?.project) {
          setProject(event.data.project);
        }
        if (event.data?.versus) {
          setVersus(event.data.versus);
        }
      };
      return () => {
        bc.close();
      };
    } catch {}
  }, []);

  const broadcastLocal = (updatedProj: TournamentProject, updatedVersus?: any) => {
    try {
      bcRef.current?.postMessage({
        project: updatedProj,
        versus: updatedVersus || versus,
      });
    } catch {}
  };

  // Server-Sent Events (SSE) if backend is present
  useEffect(() => {
    let es: EventSource | null = null;
    let reconnectTimeout: ReturnType<typeof setTimeout> | undefined;

    function connect() {
      try {
        es = new EventSource('/api/stream');
        es.onopen = () => setIsConnected(true);

        const handleMsg = (e: MessageEvent) => {
          try {
            const data = JSON.parse(e.data);
            if (data.project) setProject(data.project);
            if (data.versus) setVersus(data.versus);

            if (data.versus?.lastAction?.type === 'pick_winner' || data.versus?.lastAction?.type === 'cinematic') {
              soundFX.playVictoryFanfare();
            }
          } catch (err) {
            console.error('SSE JSON parse error:', err);
          }
        };

        es.addEventListener('connected', handleMsg);
        es.addEventListener('state_update', handleMsg);
        es.addEventListener('winner_advanced', handleMsg);
        es.addEventListener('slot_updated', handleMsg);
        es.addEventListener('versus_sync', handleMsg);
        es.addEventListener('tournament_reset', handleMsg);

        es.onerror = () => {
          setIsConnected(false);
          if (es) es.close();
        };
      } catch {
        // SSE not available (e.g. static host), perfectly fine
      }
    }

    fetch('/api/project')
      .then(res => res.json())
      .then(data => {
        if (data.project) setProject(data.project);
        if (data.versus) setVersus(data.versus);
        connect();
      })
      .catch(() => {
        // Running statically, use localStorage
        setIsConnected(true);
      });

    return () => {
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (es) es.close();
    };
  }, []);

  // Actions with local fallback
  const advanceWinner = useCallback(async (srcKey: string, dstKey: string, winnerSide?: 0 | 1, winnerName?: string) => {
    // Optimistic local update
    setProject(prev => {
      const nextSlots = { ...prev.slots };
      if (prev.slots[srcKey]) {
        nextSlots[dstKey] = { ...prev.slots[srcKey]! };
      }
      let nextElim = prev.eliminated.filter(k => k !== srcKey && k !== dstKey);
      const rival = rivalOf(srcKey);
      if (rival && prev.slots[rival] && !nextElim.includes(rival)) {
        nextElim.push(rival);
      }
      const updated = {
        ...prev,
        slots: nextSlots,
        eliminated: nextElim,
        lastUpdated: Date.now(),
      };
      broadcastLocal(updated);
      return updated;
    });

    try {
      const res = await fetch('/api/project/advance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ srcKey, dstKey, winnerSide, winnerName }),
      });
      const data = await res.json();
      if (data.project) setProject(data.project);
      if (data.versus) setVersus(data.versus);
    } catch {}
  }, []);

  const updateSlot = useCallback(async (key: string, participant: Participant | null) => {
    setProject(prev => {
      const updated = {
        ...prev,
        slots: { ...prev.slots, [key]: participant },
        lastUpdated: Date.now(),
      };
      broadcastLocal(updated);
      return updated;
    });

    try {
      await fetch('/api/project/slot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key, participant }),
      });
    } catch {}
  }, []);

  const toggleEliminated = useCallback(async (key: string) => {
    setProject(prev => {
      const nextElim = prev.eliminated.includes(key)
        ? prev.eliminated.filter(k => k !== key)
        : [...prev.eliminated, key];
      const updated = { ...prev, eliminated: nextElim };
      broadcastLocal(updated);
      return updated;
    });

    try {
      await fetch('/api/project/toggle-eliminated', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key }),
      });
    } catch {}
  }, []);

  const updateProjectSettings = useCallback(async (settings: Partial<TournamentProject>) => {
    setProject(prev => {
      const updated = { ...prev, ...settings, lastUpdated: Date.now() };
      broadcastLocal(updated);
      return updated;
    });

    try {
      await fetch('/api/project/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });
    } catch {}
  }, []);

  const syncVersus = useCallback(async (params: { isOpen?: boolean; tab?: number; matchIdx?: number; action?: any }) => {
    setVersus(prev => {
      const updated = {
        isOpen: params.isOpen !== undefined ? params.isOpen : prev.isOpen,
        tab: params.tab !== undefined ? params.tab : prev.tab,
        matchIdx: params.matchIdx !== undefined ? params.matchIdx : prev.matchIdx,
        lastAction: params.action || prev.lastAction,
      };
      try {
        bcRef.current?.postMessage({ versus: updated });
      } catch {}
      return updated;
    });

    try {
      await fetch('/api/versus/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      });
    } catch {}
  }, []);

  const resetProject = useCallback(async () => {
    const updated = JSON.parse(JSON.stringify(INITIAL_PROJECT));
    setProject(updated);
    setVersus({ isOpen: false, tab: 0, matchIdx: 0 });
    broadcastLocal(updated, { isOpen: false, tab: 0, matchIdx: 0 });

    try {
      await fetch('/api/project/reset', { method: 'POST' });
    } catch {}
  }, []);

  return {
    project,
    versus,
    isConnected,
    advanceWinner,
    updateSlot,
    toggleEliminated,
    updateProjectSettings,
    syncVersus,
    resetProject,
  };
}
