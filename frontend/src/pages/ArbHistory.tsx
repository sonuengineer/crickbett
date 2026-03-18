import { useEffect, useState } from 'react';
import { getArbHistory } from '../services/api';
import { ArbOpportunity } from '../stores/arbStore';

export default function ArbHistory() {
  const [arbs, setArbs] = useState<ArbOpportunity[]>([]);
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadHistory();
  }, [filter]);

  const loadHistory = async () => {
    try {
      const params: Record<string, string | number> = { limit: 100 };
      if (filter) params.arb_type = filter;
      const res = await getArbHistory(params);
      setArbs(res.data);
    } catch {
      // handled
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Arb History</h1>

        <div className="flex gap-2">
          {['', 'cross_book', 'back_lay', 'live_swing'].map((type) => (
            <button
              key={type}
              onClick={() => setFilter(type)}
              className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                filter === type
                  ? 'bg-emerald-500/20 text-emerald-400'
                  : 'bg-gray-800 text-gray-400 hover:text-white'
              }`}
            >
              {type ? type.replace('_', ' ').toUpperCase() : 'ALL'}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="text-center py-20 text-gray-500">Loading...</div>
      ) : arbs.length === 0 ? (
        <div className="text-center py-20 text-gray-400">
          No historical arbs found
        </div>
      ) : (
        <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-800/50 text-gray-400">
                <th className="text-left px-4 py-3">Match</th>
                <th className="text-left px-4 py-3">Type</th>
                <th className="text-left px-4 py-3">Market</th>
                <th className="text-right px-4 py-3">Profit %</th>
                <th className="text-right px-4 py-3">Stake</th>
                <th className="text-left px-4 py-3">Status</th>
                <th className="text-left px-4 py-3">Detected</th>
              </tr>
            </thead>
            <tbody>
              {arbs.map((arb, i) => (
                <tr key={arb.id || i} className="border-t border-gray-800/50 hover:bg-gray-800/30">
                  <td className="px-4 py-3 text-white">{arb.match || '-'}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-xs px-2 py-0.5 rounded ${
                        arb.arb_type === 'cross_book'
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : arb.arb_type === 'back_lay'
                            ? 'bg-blue-500/20 text-blue-400'
                            : 'bg-amber-500/20 text-amber-400'
                      }`}
                    >
                      {arb.arb_type.replace('_', ' ').toUpperCase()}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-400">
                    {arb.market_type.replace(/_/g, ' ')}
                  </td>
                  <td className="px-4 py-3 text-right text-emerald-400 font-medium">
                    {arb.profit_pct.toFixed(2)}%
                  </td>
                  <td className="px-4 py-3 text-right text-white">
                    {'\u20B9'}{arb.total_stake?.toLocaleString('en-IN') || '-'}
                  </td>
                  <td className="px-4 py-3 text-gray-400 capitalize">
                    {(arb as unknown as { status?: string }).status || '-'}
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {arb.detected_at ? new Date(arb.detected_at).toLocaleString() : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
