import { useEffect, useState } from 'react';
import { getLiveMatches, getOddsComparison } from '../services/api';
import MatchCard from '../components/MatchCard';
import OddsTable from '../components/OddsTable';

interface Match {
  id: string;
  team_a: string;
  team_b: string;
  match_status: string;
  tournament?: string;
  format?: string;
  current_score_a?: string;
  current_score_b?: string;
  start_time?: string;
}

export default function LiveMatches() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [selectedMatch, setSelectedMatch] = useState<string | null>(null);
  const [oddsData, setOddsData] = useState<unknown[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMatches();
    const interval = setInterval(loadMatches, 15000);
    return () => clearInterval(interval);
  }, []);

  const loadMatches = async () => {
    try {
      const res = await getLiveMatches();
      setMatches(res.data);
    } catch {
      // handled by interceptor
    } finally {
      setLoading(false);
    }
  };

  const loadOdds = async (matchId: string) => {
    setSelectedMatch(matchId);
    try {
      const res = await getOddsComparison(matchId);
      setOddsData(res.data);
    } catch {
      setOddsData([]);
    }
  };

  if (loading) {
    return <div className="text-center py-20 text-gray-500">Loading matches...</div>;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">Live Matches</h1>

      {matches.length === 0 ? (
        <div className="text-center py-20 text-gray-400">
          No live matches at the moment
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-3">
            {matches.map((match) => (
              <MatchCard
                key={match.id}
                match={match}
                onClick={() => loadOdds(match.id)}
              />
            ))}
          </div>

          <div>
            {selectedMatch ? (
              <OddsTable
                data={oddsData as { selection: string; bookmaker_odds: Record<string, number>; best_bookmaker: string; best_odds: number }[]}
                title="Odds Comparison"
              />
            ) : (
              <div className="bg-gray-900 rounded-xl border border-gray-800 p-8 text-center text-gray-500">
                Select a match to view odds comparison
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
