interface OddsComparisonItem {
  selection: string;
  bookmaker_odds: Record<string, number>;
  best_bookmaker: string;
  best_odds: number;
}

interface Props {
  data: OddsComparisonItem[];
  title?: string;
}

export default function OddsTable({ data, title }: Props) {
  if (!data.length) {
    return <p className="text-gray-500 text-center py-8">No odds data available</p>;
  }

  // Get all unique bookmakers
  const bookmakers = [
    ...new Set(data.flatMap((item) => Object.keys(item.bookmaker_odds))),
  ];

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
      {title && (
        <div className="px-5 py-3 border-b border-gray-800">
          <h3 className="text-lg font-semibold text-white">{title}</h3>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-800/50">
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Selection</th>
              {bookmakers.map((bk) => (
                <th key={bk} className="text-center px-4 py-3 text-gray-400 font-medium uppercase">
                  {bk}
                </th>
              ))}
              <th className="text-center px-4 py-3 text-gray-400 font-medium">Best</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item) => (
              <tr key={item.selection} className="border-t border-gray-800/50 hover:bg-gray-800/30">
                <td className="px-4 py-3 text-white font-medium">{item.selection}</td>
                {bookmakers.map((bk) => {
                  const odds = item.bookmaker_odds[bk];
                  const isBest = bk === item.best_bookmaker;
                  return (
                    <td
                      key={bk}
                      className={`text-center px-4 py-3 ${
                        isBest
                          ? 'text-emerald-400 font-bold bg-emerald-400/5'
                          : odds
                            ? 'text-white'
                            : 'text-gray-600'
                      }`}
                    >
                      {odds ? odds.toFixed(2) : '-'}
                    </td>
                  );
                })}
                <td className="text-center px-4 py-3 text-emerald-400 font-bold">
                  {item.best_odds.toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
