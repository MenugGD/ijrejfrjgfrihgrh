import { Participant, TournamentProject } from './types';

export const ROUNDS = [6, 3, 2, 1]; // Casillas por lado en cada ronda
export const ROUND_NAMES = ["Ronda 1", "Ronda 2", "Semifinal", "Finalista"];

export const VS_TABS: Array<[string, string, 'L' | 'R' | 'F', number]> = [
  ["R1 Izq", "Ronda 1 · Izquierda", "L", 0],
  ["R1 Der", "Ronda 1 · Derecha", "R", 0],
  ["R2 Izq", "Ronda 2 · Izquierda", "L", 1],
  ["R2 Der", "Ronda 2 · Derecha", "R", 1],
  ["Semi Izq", "Semifinal · Izquierda", "L", 2],
  ["Semi Der", "Semifinal · Derecha", "R", 2],
  ["Final", "Final", "F", 3],
];

// 12 curated default drawings
export const DEFAULT_PARTICIPANTS: Participant[] = [
  {
    name: 'Dragón Astral',
    detail: 'Valeria M. (Tinta y Acrílico)',
    media: 'https://images.unsplash.com/photo-1579783902614-a3fb3927b675?auto=format&fit=crop&w=800&q=80',
    fx: 0.5,
    fy: 0.5,
    zoom: 1.0,
  },
  {
    name: 'Ciber Samurái',
    detail: 'Kenji Sato (Arte Digital)',
    media: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=800&q=80',
    fx: 0.5,
    fy: 0.5,
    zoom: 1.0,
  },
  {
    name: 'Fénix Dorado',
    detail: 'Mateo R. (Óleo sobre Lienzo)',
    media: 'https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?auto=format&fit=crop&w=800&q=80',
    fx: 0.5,
    fy: 0.5,
    zoom: 1.0,
  },
  {
    name: 'Gata Mística',
    detail: 'Luna Art (Acuarela)',
    media: 'https://images.unsplash.com/photo-1541701494587-cb58502866ab?auto=format&fit=crop&w=800&q=80',
    fx: 0.5,
    fy: 0.5,
    zoom: 1.0,
  },
  {
    name: 'Guardián del Bosque',
    detail: 'Santiago P. (Ilustración Vectorial)',
    media: 'https://images.unsplash.com/photo-1550684848-fac1c5b4e853?auto=format&fit=crop&w=800&q=80',
    fx: 0.5,
    fy: 0.5,
    zoom: 1.0,
  },
  {
    name: 'Titán de Neón',
    detail: 'Zoe Pixel (Pixel Art)',
    media: 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=800&q=80',
    fx: 0.5,
    fy: 0.5,
    zoom: 1.0,
  },
  {
    name: 'Sirena del Abismo',
    detail: 'Camila Blue (Grafito y Tiza)',
    media: 'https://images.unsplash.com/photo-1563089145-599997674d42?auto=format&fit=crop&w=800&q=80',
    fx: 0.5,
    fy: 0.5,
    zoom: 1.0,
  },
  {
    name: 'Hechicero del Caos',
    detail: 'Dante Noir (Digital Painting)',
    media: 'https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?auto=format&fit=crop&w=800&q=80',
    fx: 0.5,
    fy: 0.5,
    zoom: 1.0,
  },
  {
    name: 'Caballero Cuántico',
    detail: 'Ignacio V. (Estilo Cómic)',
    media: 'https://images.unsplash.com/photo-1561214115-f2f134cc4912?auto=format&fit=crop&w=800&q=80',
    fx: 0.5,
    fy: 0.5,
    zoom: 1.0,
  },
  {
    name: 'Quimera Volcánica',
    detail: 'Solana G. (Rotuladores Alcohol)',
    media: 'https://images.unsplash.com/photo-1579783928621-7a13d66a62d1?auto=format&fit=crop&w=800&q=80',
    fx: 0.5,
    fy: 0.5,
    zoom: 1.0,
  },
  {
    name: 'Espíritu de Viento',
    detail: 'Ariadna C. (Gouache)',
    media: 'https://images.unsplash.com/photo-1549887534-1541e9326642?auto=format&fit=crop&w=800&q=80',
    fx: 0.5,
    fy: 0.5,
    zoom: 1.0,
  },
  {
    name: 'Mecha Valquiria',
    detail: 'Diego Tech (Modelado & 2D)',
    media: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=800&q=80',
    fx: 0.5,
    fy: 0.5,
    zoom: 1.0,
  },
];

export function createInitialSlots(): Record<string, Participant | null> {
  const slots: Record<string, Participant | null> = {};

  // All slots for L and R
  for (const side of ['L', 'R']) {
    for (let r = 0; r < ROUNDS.length; r++) {
      for (let i = 0; i < ROUNDS[r]; i++) {
        slots[`${side}:${r}:${i}`] = null;
      }
    }
  }
  slots['C:0:0'] = null; // Campeón

  // Populate Round 1 with the 12 participants (6 on L, 6 on R)
  for (let i = 0; i < 6; i++) {
    slots[`L:0:${i}`] = { ...DEFAULT_PARTICIPANTS[i] };
    slots[`R:0:${i}`] = { ...DEFAULT_PARTICIPANTS[i + 6] };
  }

  return slots;
}

export const INITIAL_PROJECT: TournamentProject = {
  title: 'Mi Torneo de Dibujo',
  background: {
    media: '',
    blur: 12,
    veil: 35,
  },
  chroma: null,
  transparent: false,
  slots: createInitialSlots(),
  eliminated: [],
  lastUpdated: Date.now(),
};
