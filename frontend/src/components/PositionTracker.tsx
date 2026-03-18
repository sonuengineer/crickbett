interface Position {
  id: string;
  market_type: string;
  position_status: string;
  initial_bet_bookmaker?: string;
  initial_bet_selection?: string;
  initial_bet_odds?: number;
  initial_bet_stake?: number;
  hedge_bet_bookmaker?: string;
  hedge_bet_selection?: string;
  hedge_bet_odds?: number;
  hedge_bet_stake?: number;
  guaranteed_profit?: number;
  created_at: string;
}

interface Props {
  positions: Position[];
  onClose?: (id: string) => void;
}

export default function PositionTracker({ positions, onClose }: Props) {
  if (!positions.length) {
    return (
      <div className="text-center py-12 text-gray-500">
        No positions yet. Record your first bet to start tracking.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {positions.map((pos) => (
        <div
          key={pos.id}
          className={`bg-gray-900 rounded-xl border p-4 ${
            pos.position_status === 'closed'
              ? 'border-gray-800 opacity-60'
              : pos.guaranteed_profit && pos.guaranteed_profit > 0
                ? 'border-emerald-500/30'
                : 'border-gray-800'
          }`}
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-gray-400">
              {pos.market_type.replace(/_/g, ' ').toUpperCase()}
            </span>
            <span
              className={`text-xs px-2 py-0.5 rounded-full ${
                pos.position_status === 'open'
                  ? 'bg-blue-500/20 text-blue-400'
                  : pos.position_status === 'partially_hedged'
                    ? 'bg-amber-500/20 text-amber-400'
                    : 'bg-gray-800 text-gray-400'
              }`}
            >
              {pos.position_status.replace('_', ' ').toUpperCase()}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {/* Original bet */}
            <div className="bg-gray-800/50 rounded-lg p-3">
              <p className="text-xs text-gray-400 mb-1">Original Bet</p>
              <p className="text-white">
                {pos.initial_bet_selection} @ {pos.initial_bet_odds?.toFixed(2)}
              </p>
              <p className="text-sm text-gray-400">
                {pos.initial_bet_bookmaker?.toUpperCase()} -{' '}
                {'\u20B9'}{pos.initial_bet_stake?.toLocaleString('en-IN')}
              </p>
            </div>

            {/* Hedge bet */}
            <div className="bg-gray-800/50 rounded-lg p-3">
              <p className="text-xs text-gray-400 mb-1">Hedge Bet</p>
              {pos.hedge_bet_selection ? (
                <>
                  <p className="text-white">
                    {pos.hedge_bet_selection} @ {pos.hedge_bet_odds?.toFixed(2)}
                  </p>
                  <p className="text-sm text-gray-400">
                    {pos.hedge_bet_bookmaker?.toUpperCase()} -{' '}
                    {'\u20B9'}{pos.hedge_bet_stake?.toLocaleString('en-IN')}
                  </p>
                </>
              ) : (
                <p className="text-gray-500 text-sm">Not hedged yet</p>
              )}
            </div>
          </div>

          {/* Profit + Close */}
          <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-800">
            {pos.guaranteed_profit !== null && pos.guaranteed_profit !== undefined ? (
              <span
                className={`font-bold ${
                  pos.guaranteed_profit > 0 ? 'text-emerald-400' : 'text-red-400'
                }`}
              >
                Profit: {'\u20B9'}{pos.guaranteed_profit.toLocaleString('en-IN')}
              </span>
            ) : (
              <span className="text-gray-500 text-sm">Pending hedge</span>
            )}

            {pos.position_status !== 'closed' && onClose && (
              <button
                onClick={() => onClose(pos.id)}
                className="text-sm text-gray-400 hover:text-white px-3 py-1 rounded bg-gray-800"
              >
                Close Position
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
