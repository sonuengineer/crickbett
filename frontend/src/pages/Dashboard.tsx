import { useEffect, useState } from 'react';
import { useArbStore } from '../stores/arbStore';
import { getActiveArbs } from '../services/api';
import ArbCard from '../components/ArbCard';

export default function Dashboard() {
  const { activeArbs, setActiveArbs } = useArbStore();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadArbs();
    const interval = setInterval(loadArbs, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, []);

  const loadArbs = async () => {
    try {
      const res = await getActiveArbs();
      setActiveArbs(res.data);
    } catch {
      // API errors handled by interceptor
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-gray-400 text-sm">
            Real-time arbitrage opportunities
          </p>
        </div>

        <div className="flex gap-3">
          <div className="bg-gray-900 border border-gray-800 rounded-xl px-4 py-3 text-center">
            <p className="text-2xl font-bold text-emerald-400">{activeArbs.length}</p>
            <p className="text-xs text-gray-400">Active Arbs</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl px-4 py-3 text-center">
            <p className="text-2xl font-bold text-white">
              {activeArbs.length > 0
                ? Math.max(...activeArbs.map((a) => a.profit_pct)).toFixed(2) + '%'
                : '-'}
            </p>
            <p className="text-xs text-gray-400">Best Profit</p>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-20 text-gray-500">Loading...</div>
      ) : activeArbs.length === 0 ? (
        <div className="text-center py-20">
          <p className="text-gray-400 text-lg mb-2">No active arbitrage opportunities</p>
          <p className="text-gray-600 text-sm">
            Scrapers are running. Arb alerts will appear here in real time with sound.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {activeArbs.map((arb, i) => (
            <ArbCard key={arb.id || i} arb={arb} />
          ))}
        </div>
      )}
    </div>
  );
}
