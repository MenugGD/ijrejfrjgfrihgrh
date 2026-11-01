import React, { useMemo } from 'react';
import { Participant, TournamentProject } from '../types';
import { ROUNDS, ROUND_NAMES } from '../initialData';
import { bracketCenters, bracketLinks, rivalOf } from '../utils/bracketLogic';

interface BracketCanvasProps {
  project: TournamentProject;
  zoom: number;
  onSlotClick: (key: string) => void;
  onSlotContextMenu: (key: string, e: React.MouseEvent) => void;
  onTitleChange: (newTitle: string) => void;
  onChampionStageClick?: () => void;
  isStreamMode?: boolean;
}

export const BracketCanvas: React.FC<BracketCanvasProps> = ({
  project,
  zoom,
  onSlotClick,
  onSlotContextMenu,
  onTitleChange,
  onChampionStageClick,
  isStreamMode = false,
}) => {
  const { title, slots, eliminated, chroma, transparent, background } = project;

  // Design dimensions matching python: 2408 x 1260
  const DESIGN_W = 2408;
  const DESIGN_H = 1260;
  const RATIO = 16 / 9;

  // Geometry calculations
  const { geo, layoutInfo, links } = useMemo(() => {
    const W = DESIGN_W;
    const H = DESIGN_H;
    const ui = 1.0;
    const margin = 28 * ui;
    const th = 58 * ui;
    const ty = 14 * ui;
    const lab_h = 22 * ui;
    const top = ty + th + 10 * ui + lab_h + 10 * ui;
    const bottom = H - 20 * ui;
    const avail = bottom - top;

    const nh = 20 * ui;
    const dh = 20 * ui;
    const gp = 3 * ui;
    const over = nh + dh + 2 * gp;
    const vgap = 8 * ui;
    const hgap_min = 24 * ui;

    const sw_h = (W - 2 * margin - 8 * hgap_min) / 9.0;
    const sh_v = (avail - 5 * vgap) / 6.0 - over;
    const sw = Math.max(24.0, Math.min(sw_h, sh_v * RATIO));
    const sh = sw / RATIO;
    const gap = Math.max(4.0, (W - 2 * margin - 9 * sw) / 8.0);

    const cs = bracketCenters(top, bottom);

    const computedGeo: Record<string, { x: number; y: number; w: number; h: number; imgH: number }> = {};
    for (const side of ['L', 'R']) {
      for (let r = 0; r < ROUNDS.length; r++) {
        const col = side === 'L' ? r : 8 - r;
        const x = margin + col * (sw + gap);
        for (let i = 0; i < ROUNDS[r]; i++) {
          const cy = cs[`${r}:${i}`];
          computedGeo[`${side}:${r}:${i}`] = {
            x,
            y: cy - (sh + over) / 2,
            w: sw,
            h: sh + over,
            imgH: sh,
          };
        }
      }
    }

    const cw = sw * 1.3;
    const chh = cw / RATIO + over;
    const cx = margin + 4 * (sw + gap) + sw / 2;
    const cyc = cs['3:0'];
    computedGeo['C:0:0'] = {
      x: cx - cw / 2,
      y: cyc - chh / 2,
      w: cw,
      h: chh,
      imgH: cw / RATIO,
    };

    return {
      geo: computedGeo,
      layoutInfo: { top, sw, gap, margin, lab_h, over, nh, dh, gp },
      links: bracketLinks(),
    };
  }, []);

  const champion = slots['C:0:0'];

  // Background styling
  const bgStyle = useMemo(() => {
    if (chroma) {
      return { backgroundColor: chroma };
    }
    if (transparent) {
      return isStreamMode
        ? { backgroundColor: 'transparent' }
        : {
            backgroundColor: '#3A3A3A',
            backgroundImage:
              'linear-gradient(45deg, #2E2E2E 25%, transparent 25%), linear-gradient(-45deg, #2E2E2E 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #2E2E2E 75%), linear-gradient(-45deg, transparent 75%, #2E2E2E 75%)',
            backgroundSize: '32px 32px',
            backgroundPosition: '0 0, 0 16px, 16px -16px, -16px 0px',
          };
    }
    if (background.media) {
      return {
        backgroundImage: `url(${background.media})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      };
    }
    return {
      background: 'linear-gradient(135deg, #FFFFFF 0%, #FFE6CF 100%)',
    };
  }, [chroma, transparent, background.media, isStreamMode]);

  return (
    <div
      className="relative select-none overflow-hidden transition-all duration-200"
      style={{
        width: `${DESIGN_W * zoom}px`,
        height: `${DESIGN_H * zoom}px`,
        transformOrigin: 'top left',
        ...bgStyle,
      }}
    >
      {/* Background Veil Overlay if custom image */}
      {background.media && !chroma && !transparent && (
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            backgroundColor: `rgba(255, 255, 255, ${(background.veil * 2.55) / 255})`,
            backdropFilter: background.blur > 0 ? `blur(${background.blur}px)` : 'none',
          }}
        />
      )}

      {/* Scaled contents container */}
      <div
        className="absolute inset-0"
        style={{
          width: `${DESIGN_W}px`,
          height: `${DESIGN_H}px`,
          transform: `scale(${zoom})`,
          transformOrigin: 'top left',
        }}
      >
        {/* Tournament Title */}
        <div className="absolute top-3.5 left-1/2 -translate-x-1/2 z-20">
          <input
            type="text"
            value={title}
            onChange={(e) => onTitleChange(e.target.value)}
            placeholder="Mi Torneo"
            className="text-center font-extrabold text-[#E8590C] bg-white/75 hover:bg-white/95 focus:bg-white border-2 border-transparent focus:border-[#FF7A1A] rounded-full px-8 py-2 text-3xl shadow-sm focus:outline-none transition-all"
            style={{ width: '640px' }}
          />
        </div>

        {/* Round Name Pills */}
        {['L', 'R'].map((side) =>
          ROUNDS.map((_, r) => {
            const rect = geo[`${side}:${r}:0`];
            if (!rect) return null;
            const pitch = layoutInfo.sw + layoutInfo.gap;
            const y = layoutInfo.top - 10 - layoutInfo.lab_h;

            return (
              <div
                key={`${side}:${r}`}
                className="absolute z-10 flex items-center justify-center bg-white/80 border border-white/60 rounded-full px-4 py-1 text-xs font-bold text-[#E8590C] shadow-xs"
                style={{
                  left: `${rect.x + rect.w / 2 - Math.min(pitch - 4, rect.w) / 2}px`,
                  top: `${y}px`,
                  width: `${Math.min(pitch - 4, rect.w)}px`,
                  height: `${layoutInfo.lab_h}px`,
                }}
              >
                {ROUND_NAMES[r]}
              </div>
            );
          })
        )}

        {/* CAMPEÓN Pill */}
        {geo['C:0:0'] && (
          <div
            className="absolute z-10 flex items-center justify-center bg-[#FFE08A]/95 border border-[#F5B301]/60 rounded-full px-5 py-1 text-sm font-black tracking-wider text-[#8A6100] shadow-sm"
            style={{
              left: `${geo['C:0:0'].x + geo['C:0:0'].w / 2 - 80}px`,
              top: `${geo['C:0:0'].y - 36}px`,
              width: '160px',
              height: '28px',
            }}
          >
            CAMPEÓN
          </div>
        )}

        {/* CHAMPION CINEMATIC STAGE (Above Champion Slot) */}
        {champion && (
          <div
            onClick={onChampionStageClick}
            className="absolute z-20 rounded-3xl bg-gradient-to-b from-[#150E2B] via-[#2A1226] to-[#40190A] border-2 border-[#F5B301] shadow-2xl overflow-hidden cursor-pointer p-4 flex flex-col items-center justify-between group"
            style={{
              left: `${geo['L:3:0'].x + geo['L:3:0'].w + 24}px`,
              right: `${DESIGN_W - geo['R:3:0'].x + 24}px`,
              top: `${layoutInfo.top}px`,
              bottom: `${DESIGN_H - geo['C:0:0'].y + 44}px`,
            }}
            title="Clic para repetir la animación de campeón"
          >
            {/* Header */}
            <div className="text-center">
              <span className="font-black text-2xl tracking-wider text-[#FFD84D] drop-shadow-md">
                ¡CAMPEÓN!
              </span>
            </div>

            {/* Champion Art Container with golden pulsing glow */}
            <div className="relative flex-1 max-h-[220px] aspect-[16/9] rounded-2xl overflow-hidden border-4 border-[#F5B301] shadow-2xl group-hover:scale-102 transition-transform">
              <img
                src={champion.media}
                alt={champion.name}
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
            </div>

            {/* Champion Name */}
            <div className="text-center mt-2">
              <span className="font-extrabold text-white text-xl tracking-tight block truncate">
                {champion.name}
              </span>
              {champion.detail && (
                <span className="text-xs text-neutral-300 font-medium block truncate">
                  {champion.detail}
                </span>
              )}
            </div>
          </div>
        )}

        {/* SVG CONNECTING ELBOW LINES */}
        <svg
          className="absolute inset-0 pointer-events-none"
          width={DESIGN_W}
          height={DESIGN_H}
          viewBox={`0 0 ${DESIGN_W} ${DESIGN_H}`}
        >
          {links.map(([aKey, bKey], idx) => {
            const a = geo[aKey];
            const b = geo[bKey];
            if (!a || !b) return null;
            const right = a.x + a.w / 2 < b.x + b.w / 2;
            const x1 = right ? a.x + a.w : a.x;
            const x2 = right ? b.x : b.x + b.w;
            const y1 = a.y + a.h / 2;
            const y2 = b.y + b.h / 2;
            const mx = (x1 + x2) / 2;

            return (
              <g key={idx}>
                {/* White stroke outline */}
                <path
                  d={`M ${x1} ${y1} L ${mx} ${y1} L ${mx} ${y2} L ${x2} ${y2}`}
                  stroke="rgba(255, 255, 255, 0.7)"
                  strokeWidth="7"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  fill="none"
                />
                {/* Orange inner line */}
                <path
                  d={`M ${x1} ${y1} L ${mx} ${y1} L ${mx} ${y2} L ${x2} ${y2}`}
                  stroke="#FF7A1A"
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  fill="none"
                />
              </g>
            );
          })}
        </svg>

        {/* BRACKET SLOTS */}
        {Object.entries(geo).map(([key, r]) => {
          const part = slots[key];
          const isChamp = key === 'C:0:0';
          const isEliminated = eliminated.includes(key);
          const rivalKey = rivalOf(key);
          const isAlone = rivalKey ? !slots[rivalKey] : false;

          const nh = layoutInfo.nh;
          const dh = layoutInfo.dh;
          const gp = layoutInfo.gp;

          return (
            <div
              key={key}
              onClick={() => onSlotClick(key)}
              onContextMenu={(e) => onSlotContextMenu(key, e)}
              className="absolute z-10 cursor-pointer transition-transform duration-150 hover:scale-[1.02]"
              style={{
                left: `${r.x}px`,
                top: `${r.y}px`,
                width: `${r.w}px`,
                height: `${r.h}px`,
              }}
            >
              {/* Name Pill on Top */}
              {part?.name && (
                <div
                  className="absolute top-0 left-1/2 -translate-x-1/2 bg-white/90 border border-white/80 rounded-full px-3 text-center truncate shadow-xs font-bold text-xs text-[#2B2B2B] flex items-center justify-center"
                  style={{
                    height: `${nh}px`,
                    maxWidth: `${r.w}px`,
                  }}
                >
                  {part.name}
                </div>
              )}

              {/* Main Card */}
              <div
                className={`relative w-full rounded-2xl overflow-hidden shadow-md transition-all ${
                  isChamp
                    ? 'border-3 border-[#F5B301] bg-[#FFE08A]/20'
                    : 'border-2 border-[#FF7A1A] bg-white'
                }`}
                style={{
                  marginTop: `${nh + gp}px`,
                  height: `${r.imgH}px`,
                }}
              >
                {part ? (
                  <>
                    <img
                      src={part.media}
                      alt={part.name}
                      className="w-full h-full object-cover"
                    />

                    {/* Eliminated Overlay */}
                    {isEliminated && (
                      <div className="absolute inset-0 bg-neutral-900/80 flex items-center justify-center">
                        <span className="font-extrabold text-white text-xs tracking-widest bg-red-600/90 px-2.5 py-1 rounded">
                          ELIMINADO
                        </span>
                      </div>
                    )}

                    {/* Alone (No rival) Overlay */}
                    {!isEliminated && isAlone && !isChamp && (
                      <div className="absolute inset-0 bg-neutral-800/60 flex items-center justify-center">
                        <span className="font-bold text-white text-[11px] tracking-wider bg-black/60 px-2 py-0.5 rounded">
                          SIN RIVAL
                        </span>
                      </div>
                    )}
                  </>
                ) : (
                  <div
                    className={`w-full h-full border-2 border-dashed ${
                      isChamp ? 'border-[#F5B301]' : 'border-[#FF7A1A]'
                    } rounded-2xl flex flex-col items-center justify-center text-center p-2 bg-white/70 hover:bg-white/90`}
                  >
                    {isChamp ? (
                      <span className="text-xs font-bold text-[#E8590C] leading-tight">
                        Arrastra aquí<br />al ganador
                      </span>
                    ) : (
                      <span className="text-2xl font-black text-[#FF7A1A]">+</span>
                    )}
                  </div>
                )}
              </div>

              {/* Detail Pill on Bottom */}
              {part?.detail && (
                <div
                  className="absolute bottom-0 left-1/2 -translate-x-1/2 bg-white/90 border border-white/80 rounded-full px-3 text-center truncate shadow-xs text-[11px] font-medium text-neutral-600 flex items-center justify-center"
                  style={{
                    height: `${dh}px`,
                    maxWidth: `${r.w}px`,
                  }}
                >
                  {part.detail}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
