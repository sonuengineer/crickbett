import { useState, useEffect } from 'react';
import { createHedgeMonitor, getHedgeMonitors, markHedged, deleteHedgeMonitor } from '../services/api';

interface HedgeOpp {
  opposite_selection: string;
  opposite_bookmaker: string;
  live_odds: number;
  hedge_stake: number;
  guaranteed_profit: number;
  profit_pct: number;
  breakeven_odds: number;
}

interface Monitor {
  id: string;
  match_team_a: string;
  match_team_b: string;
  tournament: string | null;
  bookmaker: string;
  selection: string;
  odds: number;
  stake: number;
  potential_return: number;
  market_type: string;
  status: string;
  breakeven_odds: number;
  best_hedge: HedgeOpp | null;
  created_at: string;
}

export default function HedgeMonitor() {
  const [monitors, setMonitors] = useState<Monitor[]>([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);

  // Form state
  const [teamA, setTeamA] = useState('');
  const [teamB, setTeamB] = useState('');
  const [tournament, setTournament] = useState('');
  const [bookmaker, setBookmaker] = useState('');
  const [selection, setSelection] = useState('');
  const [odds, setOdds] = useState('');
  const [stake, setStake] = useState('');

  const fetchMonitors = async () => {
    try {
      const res = await getHedgeMonitors();
      setMonitors(res.data);
    } catch (err) {
      console.error('Failed to fetch monitors', err);
    }
  };

  useEffect(() => {
    fetchMonitors();
    const interval = setInterval(fetchMonitors, 5000); // Refresh every 5s
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!teamA || !teamB || !bookmaker || !selection || !odds || !stake) return;

    setLoading(true);
    try {
      await createHedgeMonitor({
        match_team_a: teamA,
        match_team_b: teamB,
        tournament: tournament || undefined,
        bookmaker,
        selection,
        odds: parseFloat(odds),
        stake: parseFloat(stake),
      });
      // Reset form
      setTeamA('');
      setTeamB('');
      setTournament('');
      setBookmaker('');
      setSelection('');
      setOdds('');
      setStake('');
      setShowForm(false);
      fetchMonitors();
    } catch (err) {
      console.error('Failed to create monitor', err);
    }
    setLoading(false);
  };

  const handleHedged = async (id: string) => {
    await markHedged(id);
    fetchMonitors();
  };

  const handleDelete = async (id: string) => {
    await deleteHedgeMonitor(id);
    fetchMonitors();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'hedge_available': return 'text-yellow-400 bg-yellow-400/10';
      case 'monitoring': return 'text-blue-400 bg-blue-400/10';
      case 'hedged': return 'text-green-400 bg-green-400/10';
      default: return 'text-gray-400 bg-gray-400/10';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Live Hedge Monitor</h1>
          <p className="text-gray-400 text-sm mt-1">
            Record your pre-match bet. System monitors live odds and alerts when to hedge.
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-emerald-500 hover:bg-emerald-600 text-white px-4 py-2 rounded-lg font-semibold"
        >
          + Record New Bet
        </button>
      </div>

      {/* New Bet Form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h2 className="text-lg font-semibold text-white mb-4">Record Your Pre-Match Bet</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Team A</label>
              <input
                type="text" value={teamA} onChange={e => setTeamA(e.target.value)}
                placeholder="e.g. India" required
                className="w-full bg-gray-700 text-white rounded-lg px-3 py-2 border border-gray-600 focus:border-emerald-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Team B</label>
              <input
                type="text" value={teamB} onChange={e => setTeamB(e.target.value)}
                placeholder="e.g. Australia" required
                className="w-full bg-gray-700 text-white rounded-lg px-3 py-2 border border-gray-600 focus:border-emerald-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Tournament (optional)</label>
              <input
                type="text" value={tournament} onChange={e => setTournament(e.target.value)}
                placeholder="e.g. IPL 2025"
                className="w-full bg-gray-700 text-white rounded-lg px-3 py-2 border border-gray-600 focus:border-emerald-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Bookmaker</label>
              <input
                type="text" value={bookmaker} onChange={e => setBookmaker(e.target.value)}
                placeholder="e.g. bet365, betway, dream11" required
                className="w-full bg-gray-700 text-white rounded-lg px-3 py-2 border border-gray-600 focus:border-emerald-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">You Bet On (Selection)</label>
              <input
                type="text" value={selection} onChange={e => setSelection(e.target.value)}
                placeholder="e.g. India" required
                className="w-full bg-gray-700 text-white rounded-lg px-3 py-2 border border-gray-600 focus:border-emerald-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Odds You Got</label>
              <input
                type="number" step="0.01" value={odds} onChange={e => setOdds(e.target.value)}
                placeholder="e.g. 2.50" required
                className="w-full bg-gray-700 text-white rounded-lg px-3 py-2 border border-gray-600 focus:border-emerald-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Your Stake (Rs.)</label>
              <input
                type="number" step="1" value={stake} onChange={e => setStake(e.target.value)}
                placeholder="e.g. 1000" required
                className="w-full bg-gray-700 text-white rounded-lg px-3 py-2 border border-gray-600 focus:border-emerald-500 focus:outline-none"
              />
            </div>
            <div className="flex items-end">
              <button
                type="submit" disabled={loading}
                className="w-full bg-emerald-500 hover:bg-emerald-600 disabled:bg-gray-600 text-white py-2 rounded-lg font-semibold"
              >
                {loading ? 'Saving...' : 'Start Monitoring'}
              </button>
            </div>
          </div>

          {odds && stake && parseFloat(odds) > 1 && (
            <div className="mt-4 p-3 bg-gray-700/50 rounded-lg text-sm">
              <span className="text-gray-400">Potential return: </span>
              <span className="text-emerald-400 font-bold">
                Rs. {(parseFloat(odds) * parseFloat(stake || '0')).toFixed(2)}
              </span>
              <span className="text-gray-500 mx-2">|</span>
              <span className="text-gray-400">Breakeven opposite odds: </span>
              <span className="text-yellow-400 font-bold">
                {(parseFloat(odds) / (parseFloat(odds) - 1)).toFixed(2)}
              </span>
              <span className="text-gray-500 text-xs ml-1">
                (opposite team odds must exceed this for profit)
              </span>
            </div>
          )}
        </form>
      )}

      {/* Active Monitors */}
      {monitors.length === 0 ? (
        <div className="text-center py-16 text-gray-500">
          <p className="text-lg">No active bet monitors</p>
          <p className="text-sm mt-2">Click "Record New Bet" to start monitoring for hedge opportunities</p>
        </div>
      ) : (
        <div className="space-y-4">
          {monitors.map(m => (
            <div
              key={m.id}
              className={`bg-gray-800 rounded-xl p-5 border ${
                m.status === 'hedge_available'
                  ? 'border-yellow-500 shadow-lg shadow-yellow-500/10 animate-pulse'
                  : 'border-gray-700'
              }`}
            >
              {/* Header */}
              <div className="flex items-center justify-between mb-3">
                <div>
                  <span className="text-white font-semibold text-lg">
                    {m.match_team_a} vs {m.match_team_b}
                  </span>
                  {m.tournament && (
                    <span className="text-gray-500 text-sm ml-2">{m.tournament}</span>
                  )}
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(m.status)}`}>
                  {m.status === 'hedge_available' ? 'HEDGE NOW!' :
                   m.status === 'monitoring' ? 'Monitoring...' :
                   m.status === 'hedged' ? 'Hedged' : m.status}
                </span>
              </div>

              {/* Your Bet */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-3">
                <div>
                  <div className="text-xs text-gray-500">Your Bet</div>
                  <div className="text-white font-semibold">{m.selection}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Bookmaker</div>
                  <div className="text-white">{m.bookmaker}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Odds</div>
                  <div className="text-emerald-400 font-bold">{m.odds}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Stake</div>
                  <div className="text-white">Rs. {m.stake}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Potential Return</div>
                  <div className="text-emerald-400 font-bold">Rs. {m.potential_return.toFixed(2)}</div>
                </div>
              </div>

              <div className="text-xs text-gray-500 mb-3">
                Breakeven: opposite team odds must exceed <span className="text-yellow-400">{m.breakeven_odds.toFixed(2)}</span> for profit
              </div>

              {/* Hedge Opportunity */}
              {m.best_hedge && (
                <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 mt-2">
                  <div className="text-yellow-400 font-bold text-sm mb-2">
                    HEDGE OPPORTUNITY FOUND!
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <div>
                      <div className="text-xs text-gray-400">Bet On</div>
                      <div className="text-white font-semibold">{m.best_hedge.opposite_selection}</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-400">On Bookmaker</div>
                      <div className="text-white">{m.best_hedge.opposite_bookmaker}</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-400">Live Odds</div>
                      <div className="text-yellow-400 font-bold">{m.best_hedge.live_odds}</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-400">Hedge Stake</div>
                      <div className="text-yellow-400 font-bold">Rs. {m.best_hedge.hedge_stake}</div>
                    </div>
                  </div>
                  <div className="mt-3 p-3 bg-gray-800 rounded-lg flex items-center justify-between">
                    <div>
                      <span className="text-gray-400 text-sm">Guaranteed Profit: </span>
                      <span className="text-green-400 font-bold text-lg">
                        Rs. {m.best_hedge.guaranteed_profit}
                      </span>
                      <span className="text-green-400 text-sm ml-2">
                        ({m.best_hedge.profit_pct}%)
                      </span>
                    </div>
                    {m.status !== 'hedged' && (
                      <button
                        onClick={() => handleHedged(m.id)}
                        className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-semibold"
                      >
                        I Placed the Hedge
                      </button>
                    )}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-2 mt-3">
                {m.status === 'monitoring' && !m.best_hedge && (
                  <span className="text-blue-400 text-xs animate-pulse">
                    Watching live odds...
                  </span>
                )}
                <button
                  onClick={() => handleDelete(m.id)}
                  className="ml-auto text-red-400 hover:text-red-300 text-xs"
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* How It Works */}
      <div className="bg-gray-800/50 rounded-xl p-5 border border-gray-700">
        <h3 className="text-white font-semibold mb-3">How It Works</h3>
        <ol className="text-gray-400 text-sm space-y-2 list-decimal list-inside">
          <li>You place a <strong className="text-white">pre-match bet</strong> on any betting app (e.g., India @ 2.50 for Rs.1000)</li>
          <li>Record your bet above — system starts <strong className="text-white">monitoring live odds</strong></li>
          <li>During the match, when wickets fall or run rate changes, the opposite team's odds shift</li>
          <li>When opposite odds are high enough, you get a <strong className="text-yellow-400">HEDGE ALERT</strong> with exact stake</li>
          <li>Place the hedge bet on the recommended bookmaker for <strong className="text-green-400">guaranteed profit</strong></li>
        </ol>
      </div>
    </div>
  );
}
