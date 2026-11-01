import confetti from 'canvas-confetti';
import { AnimatePresence, motion } from 'motion/react';
import React, { useEffect, useState } from 'react';
import { VS_TABS } from '../initialData';
import { Participant } from '../types';
import { soundFX } from '../utils/audio';
import { vsInfo, vsMatches, vsPending } from '../utils/bracketLogic';

interface VersusOverlayProps {
  slots: Record<string, Participant | null>;
  tab: number;
  idx: number;
  onSelectTab: (tab: number) => void;
  onSelectIdx: (idx: number) => void;
  onAdvanceWinner: (srcKey: string, dstKey: string, winnerSide: 0 | 1, winnerName: string) => void;
  onClose: () => void;
  chroma: string | null;
  transparent: boolean;
  isObsMode?: boolean;
}

export const VersusOverlay: React.FC<VersusOverlayProps> = ({
  slots,
  tab,
  idx,
  onSelectTab,
  onSelectIdx,
  onAdvanceWinner,
  onClose,
  chroma,
  transparent,
  isObsMode = false,
}) => {
  const [animatingWinner, setAnimatingWinner] = useState<0 | 1 | null>(null);
  const [confirmDialog, setConfirmDialog] = useState<{
    side: 0 | 1;
    name: string;
    bye: boolean;
  } | null>(null);

  const matchCount = vsMatches(tab).length;
  const matchInfo = vsInfo(slots, tab, idx);
  const { pa, pb, bye, ready, winner, keyA, keyB, dstKey } = matchInfo;

  // Versus intro impact sound on change
  useEffect(() => {
    if (ready && winner === null) {
      soundFX.playVersusImpact();
    }
  }, [tab, idx, ready, winner]);

  // Handle Pick
  const handleCardClick = (side: 0 | 1) => {
    if (animatingWinner !== null || winner !== null || !ready) return;
    const participant = side === 0 ? pa : pb;
    if (!participant) return;

    setConfirmDialog({
      side,
      name: participant.name || 'este participante',
      bye,
    });
  };

  const confirmWinner = () => {
    if (!confirmDialog) return;
    const { side, name } = confirmDialog;
    setConfirmDialog(null);

    setAnimatingWinner(side);
    soundFX.playVictoryFanfare();

    // Fireworks confetti
    try {
      confetti({
        particleCount: 100,
        spread: 80,
        origin: { y: 0.5 },
        colors: ['#FFD84D', '#FF7A1A', '#FF5E8A', '#7FE3FF', '#FFFFFF'],
      });
    } catch {}

    const srcKey = side === 0 ? keyA : keyB!;

    // Complete win animation after 2.5s
    setTimeout(() => {
      onAdvanceWinner(srcKey, dstKey, side, name);
      setAnimatingWinner(null);

      // Check if Final was won
      if (dstKey === 'C:0:0') {
        onClose();
        return;
      }

      // Move to next pending match
      const next = vsPending(slots, tab, idx);
      if (next) {
        onSelectTab(next[0]);
        onSelectIdx(next[1]);
      }
    }, 2500);
  };

  // Background styling
  const bgClass = transparent
    ? 'bg-transparent'
    : chroma
    ? ''
    : 'bg-gradient-to-b from-[#150E2B] via-[#2A1226] to-[#40190A]';

  return (
    <div
      className={`fixed inset-0 z-50 flex flex-col justify-between p-4 sm:p-6 md:p-8 select-none ${bgClass}`}
      style={chroma ? { backgroundColor: chroma } : undefined}
    >
      {/* Top Tabs & Navigation (hidden in clean OBS mode) */}
      {!isObsMode && (
        <div className="flex items-center justify-between gap-3 flex-wrap z-20">
          <div className="flex items-center gap-1.5 flex-wrap">
            {VS_TABS.map(([short, full], n) => (
              <button
                key={n}
                onClick={() => {
                  onSelectTab(n);
                  onSelectIdx(0);
                }}
                title={full}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                  tab === n
                    ? 'bg-[#FF7A1A] text-white shadow-md'
                    : 'bg-white/10 hover:bg-white/20 text-white/80'
                }`}
              >
                {short}
              </button>
            ))}
          </div>

          <button
            onClick={onClose}
            className="w-10 h-10 rounded-full bg-white/20 hover:bg-white/30 text-white font-bold text-xl flex items-center justify-center transition-all cursor-pointer"
            title="Cerrar (Esc)"
          >
            ×
          </button>
        </div>
      )}

      {/* Main Versus Arena */}
      <div className="flex-1 flex flex-col items-center justify-center relative my-2">
        {/* Title / Winner Announcement */}
        <div className="text-center mb-4">
          <AnimatePresence mode="wait">
            {animatingWinner !== null || winner !== null ? (
              <motion.div
                key="winner-title"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                className="font-black text-4xl sm:text-5xl md:text-6xl text-[#FFD84D] drop-shadow-lg tracking-wider"
              >
                ¡GANADOR!
              </motion.div>
            ) : (
              <motion.div
                key="regular-title"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-white/80 font-bold text-sm tracking-wider uppercase"
              >
                {VS_TABS[tab][1]} &bull; Combate {idx + 1} de {matchCount}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Dual Cards or Not Ready Message */}
        {!ready ? (
          <div className="text-center p-8 bg-black/40 rounded-3xl border border-white/20 max-w-md">
            <p className="text-white/80 font-medium text-sm leading-relaxed">
              Faltan participantes en este combate.<br />
              Completa los combates anteriores o llena las casillas en el cuadro.
            </p>
          </div>
        ) : (
          <div className="w-full max-w-5xl flex flex-col md:flex-row items-center justify-center gap-6 md:gap-12 relative">
            {/* FIGHTER A */}
            {pa && (
              <motion.div
                onClick={() => handleCardClick(0)}
                animate={{
                  scale: animatingWinner === 0 ? 1.15 : animatingWinner === 1 ? 0.85 : 1,
                  opacity: animatingWinner === 1 ? 0.2 : 1,
                }}
                transition={{ type: 'spring', damping: 14 }}
                className={`relative flex-1 max-w-md w-full aspect-[16/10] rounded-3xl overflow-hidden cursor-pointer shadow-2xl transition-all ${
                  animatingWinner === 0 || winner === 0
                    ? 'border-4 border-[#F5B301] shadow-amber-500/50'
                    : 'border-3 border-[#FF7A1A] hover:border-white'
                }`}
              >
                <img src={pa.media} alt={pa.name} className="w-full h-full object-cover" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/30 pointer-events-none" />

                {/* Name Pill Top */}
                <div className="absolute top-3 left-1/2 -translate-x-1/2 bg-white/95 px-4 py-1 rounded-full text-xs font-black text-[#2B2B2B] shadow-md truncate max-w-[90%]">
                  {pa.name}
                </div>

                {/* Detail Pill Bottom */}
                {pa.detail && (
                  <div className="absolute bottom-3 left-1/2 -translate-x-1/2 bg-white/90 px-3 py-1 rounded-full text-[11px] font-semibold text-neutral-600 shadow-md truncate max-w-[90%]">
                    {pa.detail}
                  </div>
                )}
              </motion.div>
            )}

            {/* CENTER VS EMBLEM */}
            {!bye && (
              <div className="shrink-0 flex items-center justify-center my-2 md:my-0">
                <div className="font-heading italic text-4xl sm:text-6xl font-black text-transparent bg-clip-text bg-gradient-to-tr from-[#FFD84D] via-[#FF7A1A] to-[#FFD84D] drop-shadow-2xl animate-pulse">
                  VS
                </div>
              </div>
            )}

            {/* FIGHTER B */}
            {pb && (
              <motion.div
                onClick={() => handleCardClick(1)}
                animate={{
                  scale: animatingWinner === 1 ? 1.15 : animatingWinner === 0 ? 0.85 : 1,
                  opacity: animatingWinner === 0 ? 0.2 : 1,
                }}
                transition={{ type: 'spring', damping: 14 }}
                className={`relative flex-1 max-w-md w-full aspect-[16/10] rounded-3xl overflow-hidden cursor-pointer shadow-2xl transition-all ${
                  animatingWinner === 1 || winner === 1
                    ? 'border-4 border-[#F5B301] shadow-amber-500/50'
                    : 'border-3 border-[#FF7A1A] hover:border-white'
                }`}
              >
                <img src={pb.media} alt={pb.name} className="w-full h-full object-cover" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/30 pointer-events-none" />

                {/* Name Pill Top */}
                <div className="absolute top-3 left-1/2 -translate-x-1/2 bg-white/95 px-4 py-1 rounded-full text-xs font-black text-[#2B2B2B] shadow-md truncate max-w-[90%]">
                  {pb.name}
                </div>

                {/* Detail Pill Bottom */}
                {pb.detail && (
                  <div className="absolute bottom-3 left-1/2 -translate-x-1/2 bg-white/90 px-3 py-1 rounded-full text-[11px] font-semibold text-neutral-600 shadow-md truncate max-w-[90%]">
                    {pb.detail}
                  </div>
                )}
              </motion.div>
            )}
          </div>
        )}

        {/* Hint text */}
        {!isObsMode && ready && winner === null && (
          <p className="mt-6 text-xs text-white/60 font-medium">
            {bye
              ? 'Pasa directo a la siguiente ronda. Toca la miniatura para confirmar.'
              : 'Toca la miniatura del ganador para elegirlo'}
          </p>
        )}
      </div>

      {/* Bottom Match Navigation Buttons (hidden in clean OBS mode) */}
      {!isObsMode && (
        <div className="flex items-center justify-between z-20 pt-2 border-t border-white/10">
          <button
            onClick={() => onSelectIdx(Math.max(0, idx - 1))}
            disabled={idx === 0}
            className="px-4 py-2 bg-white/10 hover:bg-white/20 disabled:opacity-30 disabled:pointer-events-none text-white rounded-xl text-xs font-bold transition-all cursor-pointer"
          >
            ◀ Anterior
          </button>

          <span className="text-xs font-semibold text-white/70">
            {VS_TABS[tab][1]} &bull; Combate {idx + 1} de {matchCount}
          </span>

          <button
            onClick={() => onSelectIdx(Math.min(matchCount - 1, idx + 1))}
            disabled={idx === matchCount - 1}
            className="px-4 py-2 bg-white/10 hover:bg-white/20 disabled:opacity-30 disabled:pointer-events-none text-white rounded-xl text-xs font-bold transition-all cursor-pointer"
          >
            Siguiente ▶
          </button>
        </div>
      )}

      {/* CONFIRMATION POPUP MODAL */}
      <AnimatePresence>
        {confirmDialog && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-60 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4"
          >
            <div className="bg-white rounded-3xl p-6 sm:p-8 max-w-sm w-full shadow-2xl text-center space-y-4">
              <h3 className="font-extrabold text-lg text-neutral-900">
                Confirmar ganador
              </h3>

              <p className="text-sm text-neutral-600">
                {confirmDialog.bye
                  ? `¿Confirmar que «${confirmDialog.name}» pasa a la siguiente ronda?`
                  : `¿Declarar a «${confirmDialog.name}» ganador de este combate?`}
              </p>
              {!confirmDialog.bye && (
                <p className="text-xs text-neutral-400">
                  El rival quedará marcado como eliminado.
                </p>
              )}

              <div className="flex items-center justify-center gap-3 pt-2">
                <button
                  onClick={() => setConfirmDialog(null)}
                  className="flex-1 py-2.5 px-4 bg-neutral-100 hover:bg-neutral-200 text-neutral-700 font-bold text-xs rounded-full cursor-pointer transition-all"
                >
                  Cancelar
                </button>
                <button
                  onClick={confirmWinner}
                  className="flex-1 py-2.5 px-4 bg-[#FF7A1A] hover:bg-[#FF8D3A] text-white font-bold text-xs rounded-full shadow-md cursor-pointer transition-all"
                >
                  Confirmar
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
