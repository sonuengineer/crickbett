import { ArbOpportunity } from '../stores/arbStore';

const typeConfig = {
  cross_book: { label: 'CROSS-BOOK', color: 'emerald', glow: 'arb-glow' },
  back_lay: { label: 'BACK-LAY', color: 'blue', glow: 'arb-glow-blue' },
  live_swing: { label: 'LIVE HEDGE', color: 'amber', glow: 'arb-glow-orange' },
};

interface Props {
  arb: ArbOpportunity;
  onDismiss?: () => void;
}

export default function ArbCard({ arb, onDismiss }: Props) {
  const config = typeConfig[arb.arb_type as keyof typeof typeConfig] || typeConfig.cross_book;

  return (
    <div
      className={`bg-gray-900 rounded-xl border border-gray-800 p-5 animate-slide-in ${config.glow}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <span
          className={`text-xs font-bold px-2 py-1 rounded bg-${config.color}-500/20 text-${config.color}-400`}
        >
          {config.label}
        </span>
        <span className="text-2xl font-bold text-emerald-400">
          {arb.profit_pct.toFixed(2)}%
        </span>
      </div>

      {/* Match */}
      <h3 className="text-lg font-semibold text-white mb-1">{arb.match}</h3>
      <p className="text-sm text-gray-400 mb-4">
        {arb.market_type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
      </p>

      {/* Legs */}
      <div className="space-y-2 mb-4">
        {arb.legs.map((leg, i) => (
          <div key={i} className="flex items-center justify-between bg-gray-800/50 rounded-lg p-3">
            <div>
              <span className={`text-xs font-bold ${leg.side === 'back' ? 'text-blue-400' : 'text-pink-400'}`}>
                {leg.side.toUpperCase()}
              </span>
              <span className="text-white ml-2">{leg.selection}</span>
              <span className="text-gray-400 text-sm ml-2">@ {leg.odds.toFixed(2)}</span>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-400">{leg.bookmaker.toUpperCase()}</div>
              <div className="text-white font-medium">
                {'\u20B9'}{leg.stake.toLocaleString('en-IN')}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between border-t border-gray-800 pt-3">
        <div>
          <span className="text-gray-400 text-sm">Outlay: </span>
          <span className="text-white font-medium">
            {'\u20B9'}{arb.total_stake.toLocaleString('en-IN')}
          </span>
        </div>
        <div>
          <span className="text-gray-400 text-sm">Profit: </span>
          <span className="text-emerald-400 font-bold">
            {'\u20B9'}{arb.guaranteed_profit.toLocaleString('en-IN')}
          </span>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-gray-500 hover:text-red-400 text-sm"
          >
            Dismiss
          </button>
        )}
      </div>
    </div>
  );
}
