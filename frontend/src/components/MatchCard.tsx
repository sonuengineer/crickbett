interface Props {
  match: {
    id: string;
    team_a: string;
    team_b: string;
    match_status: string;
    tournament?: string;
    format?: string;
    current_score_a?: string;
    current_score_b?: string;
    start_time?: string;
  };
  onClick?: () => void;
}

export default function MatchCard({ match, onClick }: Props) {
  const isLive = match.match_status === 'live';

  return (
    <div
      onClick={onClick}
      className={`bg-gray-900 rounded-xl border p-4 cursor-pointer transition-all hover:border-gray-600 ${
        isLive ? 'border-emerald-500/50' : 'border-gray-800'
      }`}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs text-gray-400">
          {match.tournament} {match.format && `- ${match.format}`}
        </span>
        {isLive ? (
          <span className="text-xs bg-red-500/20 text-red-400 px-2 py-0.5 rounded-full font-medium animate-pulse">
            LIVE
          </span>
        ) : (
          <span className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded-full">
            {match.match_status.toUpperCase()}
          </span>
        )}
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-white font-medium">{match.team_a}</span>
          {match.current_score_a && (
            <span className="text-emerald-400 font-mono text-sm">{match.current_score_a}</span>
          )}
        </div>
        <div className="flex items-center justify-between">
          <span className="text-white font-medium">{match.team_b}</span>
          {match.current_score_b && (
            <span className="text-emerald-400 font-mono text-sm">{match.current_score_b}</span>
          )}
        </div>
      </div>

      {match.start_time && !isLive && (
        <p className="text-xs text-gray-500 mt-3">
          {new Date(match.start_time).toLocaleString()}
        </p>
      )}
    </div>
  );
}
