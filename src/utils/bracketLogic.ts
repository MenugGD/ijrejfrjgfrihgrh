import { ROUNDS, VS_TABS } from '../initialData';
import { Participant } from '../types';

export interface MatchSlotInfo {
  pa: Participant | null;
  pb: Participant | null;
  bye: boolean;
  ready: boolean;
  winner: 0 | 1 | null;
  keyA: string;
  keyB: string | null;
  dstKey: string;
}

export function bracketCenters(top: number, bottom: number): Record<string, number> {
  const pitch = (bottom - top) / 6.0;
  const r0 = [0, 1, 2, 3, 4, 5].map(i => top + pitch * (i + 0.5));
  const r1 = [(r0[0] + r0[1]) / 2, (r0[2] + r0[3]) / 2, (r0[4] + r0[5]) / 2];
  const r2 = [(r1[0] + r1[1]) / 2, r1[2]];
  const r3 = [(r2[0] + r2[1]) / 2];

  const out: Record<string, number> = {};
  const roundsList = [r0, r1, r2, r3];
  for (let r = 0; r < roundsList.length; r++) {
    for (let i = 0; i < roundsList[r].length; i++) {
      out[`${r}:${i}`] = roundsList[r][i];
    }
  }
  return out;
}

export function bracketLinks(): Array<[string, string]> {
  const links: Array<[string, string]> = [];
  for (const side of ['L', 'R']) {
    for (let r = 0; r < 3; r++) {
      for (let i = 0; i < ROUNDS[r]; i++) {
        links.push([`${side}:${r}:${i}`, `${side}:${r + 1}:${Math.floor(i / 2)}`]);
      }
    }
    links.push([`${side}:3:0`, `C:0:0`]);
  }
  return links;
}

export function vsMatches(tab: number): Array<[string, string | null, string]> {
  const [, , side, r] = VS_TABS[tab];
  if (side === 'F') {
    return [['L:3:0', 'R:3:0', 'C:0:0']];
  }
  const out: Array<[string, string | null, string]> = [];
  for (let i = 0; i < ROUNDS[r]; i += 2) {
    const b = i + 1 < ROUNDS[r] ? `${side}:${r}:${i + 1}` : null;
    out.push([`${side}:${r}:${i}`, b, `${side}:${r + 1}:${Math.floor(i / 2)}`]);
  }
  return out;
}

export function vsOrder(): Array<[number, number]> {
  const order: Array<[number, number]> = [];
  for (let r = 0; r < 3; r++) {
    const len = vsMatches(2 * r).length;
    for (let m = 0; m < len; m++) {
      order.push([2 * r, m]);
      order.push([2 * r + 1, m]);
    }
  }
  order.push([6, 0]); // Final
  return order;
}

export function rivalOf(key: string): string | null {
  const [side, rStr, iStr] = key.split(':');
  const r = parseInt(rStr, 10);
  const i = parseInt(iStr, 10);
  if (r === 3) {
    return `${side === 'L' ? 'R' : 'L'}:3:0`;
  }
  const j = i ^ 1;
  return j < ROUNDS[r] ? `${side}:${r}:${j}` : null;
}

export function vsInfo(slots: Record<string, Participant | null>, tab: number, idx: number): MatchSlotInfo {
  const matches = vsMatches(tab);
  const [keyA, keyB, dstKey] = matches[idx] || ['L:0:0', 'L:0:1', 'L:1:0'];
  const pa = slots[keyA] || null;
  const pb = keyB ? slots[keyB] || null : null;
  const bye = keyB === null;
  const ready = pa !== null && (bye || pb !== null);
  const cur = slots[dstKey] || null;

  let winner: 0 | 1 | null = null;
  if (ready && cur !== null) {
    if (cur.name === pa?.name && cur.media === pa?.media) {
      winner = 0;
    } else if (pb && cur.name === pb.name && cur.media === pb.media) {
      winner = 1;
    }
  }

  return { pa, pb, bye, ready, winner, keyA, keyB, dstKey };
}

export function vsPending(slots: Record<string, Participant | null>, tab: number, idx: number): [number, number] | null {
  const order = vsOrder();
  const currentPos = order.findIndex(([t, i]) => t === tab && i === idx);
  for (let k = 1; k <= order.length; k++) {
    const [t, i] = order[(currentPos + k) % order.length];
    if (t === tab && i === idx) continue;
    const x = vsInfo(slots, t, i);
    if (x.ready && x.winner === null) {
      return [t, i];
    }
  }
  return null;
}
