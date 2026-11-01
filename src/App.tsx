import React, { useEffect, useState } from 'react';
import { StartPage } from './components/StartPage';
import { TournamentPage } from './components/TournamentPage';
import { VersusOverlay } from './components/VersusOverlay';
import { BracketCanvas } from './components/BracketCanvas';
import { useTournamentProject } from './hooks/useTournamentProject';

export default function App() {
  const {
    project,
    versus,
    advanceWinner,
    updateSlot,
    toggleEliminated,
    updateProjectSettings,
    syncVersus,
    resetProject,
  } = useTournamentProject();

  const [currentPage, setCurrentPage] = useState<'start' | 'tournament'>('tournament');
  const [obsMode, setObsMode] = useState<boolean>(false);
  const [urlParams, setUrlParams] = useState<{ view?: string; mode?: string }>({});

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const search = new URLSearchParams(window.location.search);
      const view = search.get('view') || undefined;
      const mode = search.get('mode') || undefined;
      setUrlParams({ view, mode });
    }
  }, []);

  // OBS Standalone Browser Source View (?view=overlay)
  if (urlParams.view === 'overlay') {
    // If mode=versus or versus is active in the studio
    if (urlParams.mode === 'versus' || versus.isOpen) {
      return (
        <div className="w-screen h-screen overflow-hidden bg-transparent">
          <VersusOverlay
            slots={project.slots}
            tab={versus.tab}
            idx={versus.matchIdx}
            onSelectTab={(tab) => syncVersus({ tab, matchIdx: 0 })}
            onSelectIdx={(idx) => syncVersus({ matchIdx: idx })}
            onAdvanceWinner={(src, dst, side, name) => advanceWinner(src, dst, side, name)}
            onClose={() => syncVersus({ isOpen: false })}
            chroma={project.chroma}
            transparent={project.transparent}
            isObsMode={true}
          />
        </div>
      );
    }

    // Default OBS view: Full Bracket Canvas in 1080p
    return (
      <div className="w-screen h-screen overflow-hidden flex items-center justify-center bg-transparent">
        <BracketCanvas
          project={project}
          zoom={Math.min(window.innerWidth / 2408, window.innerHeight / 1260)}
          onSlotClick={() => {}}
          onSlotContextMenu={() => {}}
          onTitleChange={() => {}}
          isStreamMode={true}
        />
      </div>
    );
  }

  // Standard Interactive Web & Mobile App
  return (
    <div className="min-h-screen w-full bg-white text-neutral-900 font-sans-custom">
      {currentPage === 'start' ? (
        <StartPage
          onCreate={() => {
            resetProject();
            setCurrentPage('tournament');
          }}
          onLoad={() => {
            setCurrentPage('tournament');
          }}
        />
      ) : (
        <TournamentPage
          project={project}
          onUpdateProject={updateProjectSettings}
          onAdvanceWinner={(src, dst, side, name) => advanceWinner(src, dst, side, name)}
          onUpdateSlot={updateSlot}
          onToggleEliminated={toggleEliminated}
          onResetProject={resetProject}
          onOpenVersus={(tab = 0, idx = 0) => syncVersus({ isOpen: true, tab, matchIdx: idx })}
          onBackHome={() => setCurrentPage('start')}
          obsMode={obsMode}
          onToggleObsMode={() => setObsMode(!obsMode)}
        />
      )}

      {/* VERSUS OVERLAY MODAL */}
      {versus.isOpen && (
        <VersusOverlay
          slots={project.slots}
          tab={versus.tab}
          idx={versus.matchIdx}
          onSelectTab={(tab) => syncVersus({ tab, matchIdx: 0 })}
          onSelectIdx={(idx) => syncVersus({ matchIdx: idx })}
          onAdvanceWinner={(src, dst, side, name) => advanceWinner(src, dst, side, name)}
          onClose={() => syncVersus({ isOpen: false })}
          chroma={project.chroma}
          transparent={project.transparent}
          isObsMode={obsMode}
        />
      )}
    </div>
  );
}
