import React, { useState } from 'react';
import { Participant, TournamentProject } from '../types';
import { VS_TABS } from '../initialData';
import { vsInfo, vsMatches } from '../utils/bracketLogic';
import { ChevronRight, Flame, Swords, Trophy } from 'lucide-react';

interface MobileBracketViewProps {
  project: TournamentProject;
  onOpenMatch: (tab: number, idx: number) => void;
  onSlotClick: (key: string) => void;
}

export const MobileBracketView: React.FC<MobileBracketViewProps> = ({
  project,
  onOpenMatch,
  onSlotClick,
}) => {
  const [activeTab, setActiveTab] = useState<number>(0);
  const { slots, eliminated } = project;

  const matches = vsMatches(activeTab);

  return (
    <div className="w-full max-w-xl mx-auto space-y-4 select-none px-2 py-3">
      {/* Round Switcher Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-2 scrollbar-none">
        {VS_TABS.map(([short, full], n) => (
          <button
            key={n}
            onClick={() => setActiveTab(n)}
            className={`shrink-0 px-3.5 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              activeTab === n
                ? 'bg-[#FF7A1A] text-white shadow-md'
                : 'bg-white hover:bg-neutral-100 text-neutral-600 border border-neutral-200'
            }`}
          >
            {short}
          </button>
        ))}
      </div>

      <div className="flex items-center justify-between text-xs font-bold text-neutral-500 px-1">
        <span>{VS_TABS[activeTab][1]}</span>
        <span>{matches.length} {matches.length === 1 ? 'combate' : 'combates'}</span>
      </div>

      {/* Matches Cards */}
      <div className="space-y-3">
        {matches.map((m, idx) => {
          const info = vsInfo(slots, activeTab, idx);
          const { pa, pb, bye, ready, winner, keyA, keyB } = info;

          const isElimA = eliminated.includes(keyA);
          const isElimB = keyB ? eliminated.includes(keyB) : false;

          return (
            <div
              key={idx}
              className="bg-white rounded-2xl border-2 border-neutral-200 hover:border-[#FF7A1A]/70 p-3.5 shadow-sm space-y-3 transition-all"
            >
              <div className="flex items-center justify-between text-xs font-extrabold text-[#E8590C]">
                <span>Combate #{idx + 1}</span>
                {winner !== null && (
                  <span className="bg-amber-100 text-amber-800 text-[10px] font-black px-2 py-0.5 rounded-full flex items-center gap-1">
                    <Trophy className="w-3 h-3 text-amber-600" />
                    Ganador: {winner === 0 ? pa?.name : pb?.name}
                  </span>
                )}
              </div>

              {/* Matchup Duelists */}
              <div className="grid grid-cols-11 items-center gap-2">
                {/* Entrant A */}
                <div
                  onClick={() => onSlotClick(keyA)}
                  className={`col-span-5 rounded-xl border p-2 flex items-center gap-2 cursor-pointer transition-all ${
                    winner === 0
                      ? 'border-[#F5B301] bg-amber-50/70 shadow-xs'
                      : isElimA
                      ? 'border-neutral-200 bg-neutral-100 opacity-60'
                      : 'border-neutral-200 bg-white hover:border-[#FF7A1A]'
                  }`}
                >
                  <img
                    src={pa?.media || 'https://images.unsplash.com/photo-1579783902614-a3fb3927b675?auto=format&fit=crop&w=400&q=80'}
                    alt=""
                    className="w-10 h-10 rounded-lg object-cover shrink-0"
                  />
                  <div className="min-w-0 flex-1">
                    <span className="font-bold text-xs text-neutral-900 block truncate">
                      {pa?.name || 'Vacío'}
                    </span>
                    <span className="text-[10px] text-neutral-500 block truncate">
                      {pa?.detail || keyA}
                    </span>
                  </div>
                </div>

                {/* VS Badge */}
                <div className="col-span-1 text-center font-heading italic text-xs font-black text-[#FF7A1A]">
                  VS
                </div>

                {/* Entrant B */}
                <div
                  onClick={() => keyB && onSlotClick(keyB)}
                  className={`col-span-5 rounded-xl border p-2 flex items-center gap-2 cursor-pointer transition-all ${
                    bye
                      ? 'border-dashed border-neutral-300 bg-neutral-50 justify-center text-center'
                      : winner === 1
                      ? 'border-[#F5B301] bg-amber-50/70 shadow-xs'
                      : isElimB
                      ? 'border-neutral-200 bg-neutral-100 opacity-60'
                      : 'border-neutral-200 bg-white hover:border-[#FF7A1A]'
                  }`}
                >
                  {bye ? (
                    <span className="text-[11px] font-bold text-neutral-400">Pasa directo</span>
                  ) : (
                    <>
                      <img
                        src={pb?.media || 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=400&q=80'}
                        alt=""
                        className="w-10 h-10 rounded-lg object-cover shrink-0"
                      />
                      <div className="min-w-0 flex-1">
                        <span className="font-bold text-xs text-neutral-900 block truncate">
                          {pb?.name || 'Vacío'}
                        </span>
                        <span className="text-[10px] text-neutral-500 block truncate">
                          {pb?.detail || keyB}
                        </span>
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* Quick Launch Button */}
              {ready && (
                <button
                  onClick={() => onOpenMatch(activeTab, idx)}
                  className="w-full py-2 px-3 bg-gradient-to-r from-[#FF7A1A] to-[#FF8D3A] hover:from-[#FF8D3A] hover:to-[#FFA05A] text-white font-extrabold text-xs rounded-xl shadow-xs flex items-center justify-center gap-1.5 cursor-pointer active:scale-98 transition-all"
                >
                  <Swords className="w-3.5 h-3.5" />
                  Abrir Animación Versus
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
