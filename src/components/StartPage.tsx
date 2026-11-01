import React, { useEffect, useState } from 'react';
import { bracketCenters, bracketLinks } from '../utils/bracketLogic';
import { ROUNDS } from '../initialData';

interface StartPageProps {
  onCreate: () => void;
  onLoad: () => void;
}

export const StartPage: React.FC<StartPageProps> = ({ onCreate, onLoad }) => {
  const [t, setT] = useState<number>(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setT(prev => prev + 0.09);
    }, 33);
    return () => clearInterval(timer);
  }, []);

  // Compute mini bracket for decorative orange panel
  const miniW = 480;
  const miniH = 440;
  const innerTop = 35;
  const innerBottom = miniH - 35;
  const cs = bracketCenters(innerTop, innerBottom);
  const cw = miniW / 9.0;
  const bw = cw * 0.72;
  const bh = Math.min(bw * 0.72, ((miniH - 70) / 6.0) * 0.65);

  const geo: Record<string, { x: number; y: number; w: number; h: number }> = {};
  for (const side of ['L', 'R']) {
    for (let r = 0; r < ROUNDS.length; r++) {
      const col = side === 'L' ? r : 8 - r;
      for (let i = 0; i < ROUNDS[r]; i++) {
        geo[`${side}:${r}:${i}`] = {
          x: col * cw + (cw - bw) / 2,
          y: cs[`${r}:${i}`] - bh / 2,
          w: bw,
          h: bh,
        };
      }
    }
  }
  const cwid = bw * 1.3;
  geo['C:0:0'] = {
    x: 4 * cw + (cw - cwid) / 2,
    y: cs['3:0'] - (bh * 1.3) / 2,
    w: cwid,
    h: bh * 1.3,
  };

  const links = bracketLinks();

  return (
    <div className="relative w-full min-h-screen bg-white text-neutral-900 flex items-center justify-center p-6 md:p-12 overflow-hidden select-none">
      <div className="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        {/* Left column: Title, branding & action buttons */}
        <div className="lg:col-span-6 space-y-6">
          <div className="relative inline-block">
            <h1 className="text-6xl sm:text-7xl md:text-8xl font-black tracking-tight leading-none text-[#2B2B2B]">
              Tournament
              <span className="block text-[#FF7A1A]">Maker</span>
            </h1>

            {/* Minecraft-style vibrating badge */}
            <div
              className="absolute -top-3 left-[70%] sm:left-[75%] whitespace-nowrap transform -rotate-18"
              style={{
                transform: `rotate(-18deg) scale(${1 + 0.06 * Math.sin(t)})`,
              }}
            >
              <span className="font-extrabold text-sm sm:text-base text-[#E8590C] drop-shadow-sm px-2 py-0.5 rounded">
                creado por ZABA
              </span>
            </div>
          </div>

          <p className="text-lg sm:text-xl text-neutral-500 font-medium">
            Torneos de 12 participantes, a tu manera.
          </p>

          <div className="space-y-4 pt-4 max-w-xs">
            <button
              onClick={onCreate}
              className="w-full py-4 px-8 bg-[#FF7A1A] hover:bg-[#FF8D3A] active:bg-[#E8590C] text-white font-bold text-lg rounded-full shadow-lg hover:shadow-orange-500/25 transition-all transform active:scale-98 cursor-pointer"
            >
              Crear torneo
            </button>

            <button
              onClick={onLoad}
              className="w-full py-4 px-8 bg-white hover:bg-[#FFF1E6] active:bg-[#FFE0C7] text-[#E8590C] border-2 border-[#FF7A1A] font-bold text-lg rounded-full shadow-sm transition-all transform active:scale-98 cursor-pointer"
            >
              Cargar torneo
            </button>
          </div>
        </div>

        {/* Right column: Decorative panel with miniature interactive bracket */}
        <div className="lg:col-span-6 flex justify-center">
          <div className="relative w-full max-w-[520px] aspect-[16/14] bg-gradient-to-br from-[#FF9A3D] to-[#FF6A00] rounded-3xl p-6 shadow-2xl overflow-hidden flex items-center justify-center">
            {/* SVG Connecting lines */}
            <svg className="w-full h-full" viewBox={`0 0 ${miniW} ${miniH}`}>
              {links.map(([aKey, bKey], idx) => {
                const a = geo[aKey];
                const b = geo[bKey];
                if (!a || !b) return null;
                const ax = a.x < b.x ? a.x + a.w : a.x;
                const bx = a.x < b.x ? b.x : b.x + b.w;
                const ay = a.y + a.h / 2;
                const by = b.y + b.h / 2;
                const mx = (ax + bx) / 2;

                return (
                  <path
                    key={idx}
                    d={`M ${ax} ${ay} L ${mx} ${ay} L ${mx} ${by} L ${bx} ${by}`}
                    stroke="rgba(255, 255, 255, 0.7)"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    fill="none"
                  />
                );
              })}

              {/* Slots */}
              {Object.entries(geo).map(([key, r]) => {
                const isChamp = key === 'C:0:0';
                return (
                  <rect
                    key={key}
                    x={r.x}
                    y={r.y}
                    width={r.w}
                    height={r.h}
                    rx="6"
                    ry="6"
                    fill={isChamp ? '#FFE08A' : 'rgba(255, 255, 255, 0.9)'}
                    className="transition-transform duration-300 hover:scale-105"
                  />
                );
              })}
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
};
