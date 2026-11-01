import React, { useRef, useState } from 'react';
import { Camera, ChevronDown, Edit2, Layers, Maximize2, Minus, Palette, Plus, Smartphone, Sparkles, Swords, Trophy, Undo2, ZoomIn } from 'lucide-react';
import { Participant, TournamentProject } from '../types';
import { BackgroundDialog } from './BackgroundDialog';
import { BracketCanvas } from './BracketCanvas';
import { MobileBracketView } from './MobileBracketView';
import { SlotPreviewModal } from './SlotPreviewModal';

interface TournamentPageProps {
  project: TournamentProject;
  onUpdateProject: (settings: Partial<TournamentProject>) => void;
  onAdvanceWinner: (srcKey: string, dstKey: string, winnerSide: 0 | 1, winnerName: string) => void;
  onUpdateSlot: (key: string, participant: Participant | null) => void;
  onToggleEliminated: (key: string) => void;
  onResetProject: () => void;
  onOpenVersus: (tab?: number, idx?: number) => void;
  onBackHome: () => void;
  obsMode: boolean;
  onToggleObsMode: () => void;
}

export const TournamentPage: React.FC<TournamentPageProps> = ({
  project,
  onUpdateProject,
  onAdvanceWinner,
  onUpdateSlot,
  onToggleEliminated,
  onResetProject,
  onOpenVersus,
  onBackHome,
  obsMode,
  onToggleObsMode,
}) => {
  const [zoom, setZoom] = useState<number>(0.65);
  const [menuOpen, setMenuOpen] = useState<boolean>(false);
  const [obsSubmenuOpen, setObsSubmenuOpen] = useState<boolean>(false);
  const [showBgDialog, setShowBgDialog] = useState<boolean>(false);
  const [selectedSlotKey, setSelectedSlotKey] = useState<string | null>(null);
  const [mobileViewMode, setMobileViewMode] = useState<'canvas' | 'list'>('canvas');
  const [copiedObsUrl, setCopiedObsUrl] = useState<boolean>(false);

  const containerRef = useRef<HTMLDivElement>(null);

  // Zoom handlers
  const handleZoom = (delta: number) => {
    setZoom((prev) => Math.max(0.25, Math.min(2.0, prev + delta)));
  };

  const handleFit = () => {
    if (containerRef.current) {
      const containerW = containerRef.current.clientWidth;
      const containerH = containerRef.current.clientHeight;
      const fitZoom = Math.min(containerW / 2408, containerH / 1260) * 0.95;
      setZoom(Math.max(0.2, fitZoom));
    } else {
      setZoom(0.5);
    }
  };

  const copyObsUrl = () => {
    const url = `${window.location.origin}?view=overlay`;
    navigator.clipboard.writeText(url);
    setCopiedObsUrl(true);
    setTimeout(() => setCopiedObsUrl(false), 2500);
  };

  // Export Screenshot
  const handleScreenshot = () => {
    alert('Para capturar el cuadro en alta resolución o usarlo en stream, puedes usar la Fuente de Navegador de OBS o guardar la imagen.');
  };

  return (
    <div className="relative w-full h-screen overflow-hidden flex flex-col bg-[#F8F9FA] select-none">
      {/* TOP BAR (Hidden in OBS mode) */}
      {!obsMode && (
        <header className="z-30 bg-white/90 border-b border-neutral-200 backdrop-blur-md px-3 sm:px-6 py-2.5 flex items-center justify-between gap-2 shrink-0">
          {/* File Menu & Status */}
          <div className="flex items-center gap-3">
            <div className="relative">
              <button
                onClick={() => setMenuOpen(!menuOpen)}
                className="flex items-center gap-1.5 px-4 py-2 bg-white hover:bg-[#FFF1E6] text-[#E8590C] border-2 border-[#FF7A1A] font-bold text-xs sm:text-sm rounded-full shadow-xs cursor-pointer transition-all"
              >
                Archivo <ChevronDown className="w-3.5 h-3.5" />
              </button>

              {/* Dropdown Menu */}
              {menuOpen && (
                <div className="absolute top-full left-0 mt-1.5 w-64 bg-white border border-[#FFD2AE] rounded-2xl shadow-xl p-2 z-50 text-xs font-semibold text-neutral-800 space-y-1">
                  <button
                    onClick={() => {
                      setMenuOpen(false);
                      onOpenVersus();
                    }}
                    className="w-full text-left px-3 py-2 rounded-xl hover:bg-[#FFE6D1] text-[#E8590C] font-bold flex items-center justify-between cursor-pointer"
                  >
                    <span>Combates por rondas…</span>
                    <span className="text-[10px] text-neutral-400">F6</span>
                  </button>

                  <div className="my-1 border-t border-neutral-100" />

                  {/* OBS Submenu */}
                  <div className="relative">
                    <button
                      onClick={() => setObsSubmenuOpen(!obsSubmenuOpen)}
                      className="w-full text-left px-3 py-2 rounded-xl hover:bg-[#FFF1E6] flex items-center justify-between cursor-pointer"
                    >
                      <span className="flex items-center gap-1.5 text-neutral-800">
                        <Layers className="w-3.5 h-3.5 text-[#FF7A1A]" />
                        Para OBS
                      </span>
                      <ChevronDown className="w-3 h-3 text-neutral-400" />
                    </button>

                    {obsSubmenuOpen && (
                      <div className="ml-2 pl-2 border-l border-orange-200 space-y-1 my-1">
                        <button
                          onClick={() => {
                            setMenuOpen(false);
                            onToggleObsMode();
                          }}
                          className="w-full text-left px-2 py-1.5 rounded-lg hover:bg-[#FFF1E6] text-neutral-700 block"
                        >
                          Modo OBS (ocultar controles)
                        </button>
                        <button
                          onClick={() => onUpdateProject({ chroma: null })}
                          className="w-full text-left px-2 py-1.5 rounded-lg hover:bg-[#FFF1E6] text-neutral-700 block"
                        >
                          Fondo normal
                        </button>
                        <button
                          onClick={() => onUpdateProject({ chroma: '#00FF00' })}
                          className="w-full text-left px-2 py-1.5 rounded-lg hover:bg-[#FFF1E6] text-emerald-600 font-bold block"
                        >
                          Verde Croma (#00FF00)
                        </button>
                        <button
                          onClick={() => onUpdateProject({ chroma: '#0000FF' })}
                          className="w-full text-left px-2 py-1.5 rounded-lg hover:bg-[#FFF1E6] text-blue-600 font-bold block"
                        >
                          Azul Croma (#0000FF)
                        </button>
                        <button
                          onClick={() => onUpdateProject({ transparent: !project.transparent })}
                          className="w-full text-left px-2 py-1.5 rounded-lg hover:bg-[#FFF1E6] text-neutral-700 block"
                        >
                          {project.transparent ? 'Quitar transparencia' : 'Fondo transparente'}
                        </button>
                        <button
                          onClick={copyObsUrl}
                          className="w-full text-left px-2 py-1.5 rounded-lg hover:bg-[#FFF1E6] text-[#E8590C] font-bold block"
                        >
                          {copiedObsUrl ? '¡URL Copiada!' : 'Copiar URL para OBS'}
                        </button>
                      </div>
                    )}
                  </div>

                  <div className="my-1 border-t border-neutral-100" />

                  <a
                    href="/tournament_maker.zip"
                    download="tournament_maker.zip"
                    className="w-full text-left px-3 py-2 rounded-xl hover:bg-emerald-50 text-emerald-700 font-bold flex items-center justify-between cursor-pointer"
                  >
                    <span>📦 Descargar .ZIP listo para deploy</span>
                  </a>

                  <div className="my-1 border-t border-neutral-100" />

                  <button
                    onClick={() => {
                      if (confirm('¿Reiniciar todo el torneo?')) {
                        onResetProject();
                        setMenuOpen(false);
                      }
                    }}
                    className="w-full text-left px-3 py-2 rounded-xl hover:bg-red-50 text-red-600 block cursor-pointer"
                  >
                    Reiniciar Torneo
                  </button>

                  <button
                    onClick={() => {
                      setMenuOpen(false);
                      onBackHome();
                    }}
                    className="w-full text-left px-3 py-2 rounded-xl hover:bg-neutral-100 text-neutral-600 block cursor-pointer"
                  >
                    Volver al inicio
                  </button>
                </div>
              )}
            </div>

            {/* Title / Save status */}
            <span className="hidden sm:inline-block text-xs font-semibold text-neutral-400">
              {project.title || 'Torneo'}
            </span>
          </div>

          {/* Right Header Actions: Mobile View Switcher & Combates Button */}
          <div className="flex items-center gap-2">
            {/* Mobile View Toggle */}
            <div className="flex lg:hidden bg-neutral-100 p-0.5 rounded-full border border-neutral-200">
              <button
                onClick={() => setMobileViewMode('canvas')}
                className={`px-2.5 py-1 rounded-full text-xs font-bold transition-all ${
                  mobileViewMode === 'canvas' ? 'bg-[#FF7A1A] text-white' : 'text-neutral-500'
                }`}
              >
                Cuadro
              </button>
              <button
                onClick={() => setMobileViewMode('list')}
                className={`px-2.5 py-1 rounded-full text-xs font-bold transition-all ${
                  mobileViewMode === 'list' ? 'bg-[#FF7A1A] text-white' : 'text-neutral-500'
                }`}
              >
                Lista Móvil
              </button>
            </div>

            {/* ⚔ Combates Button */}
            <button
              onClick={() => onOpenVersus()}
              className="flex items-center gap-1.5 px-4 sm:px-5 py-2 bg-[#FFF1E6] hover:bg-[#FFE0C7] text-[#E8590C] rounded-full font-bold text-xs sm:text-sm cursor-pointer shadow-xs transition-all active:scale-98"
            >
              <Swords className="w-4 h-4 text-[#FF7A1A]" />
              <span>⚔ Combates</span>
            </button>
          </div>
        </header>
      )}

      {/* OBS Mode Exit Banner */}
      {obsMode && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-50 bg-black/80 text-white text-xs font-bold px-4 py-2 rounded-full shadow-xl flex items-center gap-2">
          <span>Modo OBS activado</span>
          <button
            onClick={onToggleObsMode}
            className="text-[#FF7A1A] hover:underline cursor-pointer"
          >
            Salir (F10)
          </button>
        </div>
      )}

      {/* MAIN VIEW AREA */}
      <div
        ref={containerRef}
        className="flex-1 w-full h-full overflow-auto relative flex items-center justify-center p-2 sm:p-4"
      >
        {mobileViewMode === 'list' ? (
          <div className="w-full h-full overflow-y-auto">
            <MobileBracketView
              project={project}
              onOpenMatch={(tab, idx) => onOpenVersus(tab, idx)}
              onSlotClick={(key) => setSelectedSlotKey(key)}
            />
          </div>
        ) : (
          <div className="m-auto">
            <BracketCanvas
              project={project}
              zoom={zoom}
              onSlotClick={(key) => setSelectedSlotKey(key)}
              onSlotContextMenu={(key, e) => {
                e.preventDefault();
                setSelectedSlotKey(key);
              }}
              onTitleChange={(t) => onUpdateProject({ title: t })}
              onChampionStageClick={() => onOpenVersus(6, 0)}
              isStreamMode={obsMode}
            />
          </div>
        )}
      </div>

      {/* BOTTOM FLOATING CONTROLS (Hidden in OBS mode or List mode) */}
      {!obsMode && mobileViewMode === 'canvas' && (
        <footer className="z-30 absolute bottom-4 left-4 right-4 flex items-center justify-between pointer-events-none">
          {/* Zoom Bar */}
          <div className="pointer-events-auto bg-white/95 border-2 border-[#FF7A1A] rounded-full px-3 py-1.5 shadow-lg flex items-center gap-2">
            <button
              onClick={() => handleZoom(-0.1)}
              className="w-8 h-8 rounded-full hover:bg-[#FFE6D1] text-[#E8590C] font-black text-lg flex items-center justify-center transition-colors cursor-pointer"
              title="Alejar"
            >
              <Minus className="w-4 h-4" />
            </button>

            <span className="font-bold text-xs text-[#E8590C] min-w-[48px] text-center">
              {Math.round(zoom * 100)}%
            </span>

            <button
              onClick={() => handleZoom(0.1)}
              className="w-8 h-8 rounded-full hover:bg-[#FFE6D1] text-[#E8590C] font-black text-lg flex items-center justify-center transition-colors cursor-pointer"
              title="Acercar"
            >
              <Plus className="w-4 h-4" />
            </button>

            <button
              onClick={handleFit}
              className="px-2.5 py-1 bg-[#FFF1E6] hover:bg-[#FFE0C7] text-[#E8590C] rounded-full text-xs font-bold transition-colors cursor-pointer"
              title="Ajustar a pantalla"
            >
              Ajustar
            </button>
          </div>

          {/* Background and Screenshot Floating Round Buttons */}
          <div className="pointer-events-auto flex items-center gap-2">
            <button
              onClick={() => setShowBgDialog(true)}
              className="w-12 h-12 rounded-full bg-white hover:bg-[#FFF1E6] border-2 border-[#FF7A1A] text-[#E8590C] shadow-lg flex items-center justify-center transition-all cursor-pointer"
              title="Fondo personalizado"
            >
              <Palette className="w-5 h-5 text-[#FF7A1A]" />
            </button>

            <button
              onClick={copyObsUrl}
              className="w-12 h-12 rounded-full bg-white hover:bg-[#FFF1E6] border-2 border-[#FF7A1A] text-[#E8590C] shadow-lg flex items-center justify-center transition-all cursor-pointer"
              title="Copiar link para OBS"
            >
              <Layers className="w-5 h-5 text-[#FF7A1A]" />
            </button>
          </div>
        </footer>
      )}

      {/* BACKGROUND DIALOG MODAL */}
      {showBgDialog && (
        <BackgroundDialog
          currentBg={project.background}
          onSave={(bg) => onUpdateProject({ background: bg })}
          onClose={() => setShowBgDialog(false)}
        />
      )}

      {/* SLOT EDIT / PREVIEW MODAL */}
      {selectedSlotKey && (
        <SlotPreviewModal
          slotKey={selectedSlotKey}
          participant={project.slots[selectedSlotKey]}
          isEliminated={project.eliminated.includes(selectedSlotKey)}
          onSave={(part) => {
            onUpdateSlot(selectedSlotKey, part);
            setSelectedSlotKey(null);
          }}
          onToggleEliminated={() => onToggleEliminated(selectedSlotKey)}
          onClose={() => setSelectedSlotKey(null)}
        />
      )}
    </div>
  );
};
