export interface Participant {
  name: string;
  detail: string;
  media: string;
  fx: number;
  fy: number;
  zoom: number;
}

export type SlotKey = string; // Format: "L:0:0", "R:1:2", "C:0:0"

export interface TournamentProject {
  title: string;
  background: {
    media: string;
    blur: number;
    veil: number;
  };
  chroma: string | null; // e.g. '#00FF00', '#FF00FF', '#0000FF', null
  transparent: boolean;
  slots: Record<SlotKey, Participant | null>;
  eliminated: string[]; // List of slot keys marked as eliminated
  lastUpdated: number;
}

export interface VersusState {
  isOpen: boolean;
  tab: number; // 0..6
  matchIdx: number;
}
