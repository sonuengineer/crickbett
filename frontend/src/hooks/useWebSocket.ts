import { useEffect } from 'react';
import { arbSocket } from '../services/websocket';
import { useArbStore, ArbOpportunity } from '../stores/arbStore';
import { useAuthStore } from '../stores/authStore';

export function useWebSocket() {
  const { token } = useAuthStore();
  const { addArb, soundEnabled } = useArbStore();

  useEffect(() => {
    if (!token) return;

    arbSocket.connect(token);

    const handleArb = (data: Record<string, unknown>) => {
      const arb = data as unknown as ArbOpportunity;
      addArb(arb);

      // Play sound
      if (soundEnabled) {
        playAlertSound();
      }

      // Browser notification
      if (Notification.permission === 'granted') {
        new Notification(`ARB: ${arb.profit_pct.toFixed(2)}% Profit`, {
          body: `${arb.match} - ${arb.arb_type.replace('_', ' ').toUpperCase()}`,
          icon: '/vite.svg',
        });
      }
    };

    const handleHedge = (data: Record<string, unknown>) => {
      // Play a different sound for hedge alerts
      if (soundEnabled) {
        playHedgeSound();
      }

      // Browser notification
      if (Notification.permission === 'granted') {
        const d = data as { opposite_selection?: string; guaranteed_profit?: number; hedge_stake?: number };
        new Notification(`HEDGE NOW! Profit Rs.${d.guaranteed_profit}`, {
          body: `Bet Rs.${d.hedge_stake} on ${d.opposite_selection}`,
          icon: '/vite.svg',
          requireInteraction: true,
        });
      }
    };

    arbSocket.on('arb_detected', handleArb);
    arbSocket.on('hedge_available', handleHedge);

    return () => {
      arbSocket.off('arb_detected', handleArb);
      arbSocket.off('hedge_available', handleHedge);
      arbSocket.disconnect();
    };
  }, [token, soundEnabled, addArb]);
}

function playAlertSound() {
  try {
    const ctx = new AudioContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.frequency.value = 880;
    osc.type = 'sine';
    gain.gain.value = 0.3;
    osc.start();
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.5);
    osc.stop(ctx.currentTime + 0.5);
  } catch {
    // Audio context might be blocked
  }
}

function playHedgeSound() {
  try {
    const ctx = new AudioContext();
    // Double beep for hedge alerts
    [0, 0.3].forEach(offset => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.frequency.value = 1200;
      osc.type = 'square';
      gain.gain.value = 0.2;
      osc.start(ctx.currentTime + offset);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + offset + 0.2);
      osc.stop(ctx.currentTime + offset + 0.2);
    });
  } catch {
    // Audio context might be blocked
  }
}
