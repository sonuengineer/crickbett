import { create } from 'zustand';

export interface ArbLeg {
  bookmaker: string;
  selection: string;
  odds: number;
  side: string;
  stake: number;
}

export interface ArbOpportunity {
  id?: string;
  arb_type: string;
  profit_pct: number;
  match: string;
  market_type: string;
  total_stake: number;
  guaranteed_profit: number;
  legs: ArbLeg[];
  detected_at?: string;
}

interface ArbState {
  activeArbs: ArbOpportunity[];
  arbHistory: ArbOpportunity[];
  soundEnabled: boolean;
  addArb: (arb: ArbOpportunity) => void;
  removeArb: (id: string) => void;
  setActiveArbs: (arbs: ArbOpportunity[]) => void;
  setArbHistory: (arbs: ArbOpportunity[]) => void;
  toggleSound: () => void;
}

export const useArbStore = create<ArbState>((set) => ({
  activeArbs: [],
  arbHistory: [],
  soundEnabled: true,

  addArb: (arb) =>
    set((state) => ({
      activeArbs: [arb, ...state.activeArbs].slice(0, 50),
    })),

  removeArb: (id) =>
    set((state) => ({
      activeArbs: state.activeArbs.filter((a) => a.id !== id),
    })),

  setActiveArbs: (arbs) => set({ activeArbs: arbs }),

  setArbHistory: (arbs) => set({ arbHistory: arbs }),

  toggleSound: () => set((state) => ({ soundEnabled: !state.soundEnabled })),
}));
