import { useEffect, useState } from 'react';
import { getArbSettings, updateArbSettings } from '../services/api';
import toast from 'react-hot-toast';

interface ArbSettings {
  min_profit_pct: number;
  max_stake: number;
  monitored_bookmakers: string[];
  monitored_markets: string[];
  monitored_formats: string[];
  telegram_alerts: boolean;
  web_push_alerts: boolean;
  sound_alerts: boolean;
}

const ALL_BOOKMAKERS = ['bet365', 'betfair', 'pinnacle', '1xbet', 'betway'];
const ALL_MARKETS = ['match_winner', 'total_runs', 'team_runs', 'session_runs', 'top_batsman'];
const ALL_FORMATS = ['T20', 'ODI', 'TEST'];

export default function Settings() {
  const [settings, setSettings] = useState<ArbSettings | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const res = await getArbSettings();
      setSettings(res.data);
    } catch {
      // handled
    } finally {
      setLoading(false);
    }
  };

  const save = async () => {
    if (!settings) return;
    try {
      await updateArbSettings(settings);
      toast.success('Settings saved');
    } catch {
      toast.error('Failed to save settings');
    }
  };

  if (loading || !settings) {
    return <div className="text-center py-20 text-gray-500">Loading...</div>;
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-white mb-6">Alert Settings</h1>

      <div className="space-y-6">
        {/* Profit threshold */}
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
          <h3 className="text-white font-medium mb-3">Minimum Profit %</h3>
          <input
            type="number"
            step="0.1"
            value={settings.min_profit_pct}
            onChange={(e) => setSettings({ ...settings, min_profit_pct: parseFloat(e.target.value) })}
            className="w-32 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white"
          />
          <p className="text-sm text-gray-400 mt-1">Only alert when profit exceeds this threshold</p>
        </div>

        {/* Max stake */}
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
          <h3 className="text-white font-medium mb-3">Max Stake (INR)</h3>
          <input
            type="number"
            value={settings.max_stake}
            onChange={(e) => setSettings({ ...settings, max_stake: parseFloat(e.target.value) })}
            className="w-40 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white"
          />
        </div>

        {/* Bookmakers */}
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
          <h3 className="text-white font-medium mb-3">Monitored Bookmakers</h3>
          <div className="flex flex-wrap gap-2">
            {ALL_BOOKMAKERS.map((bk) => (
              <button
                key={bk}
                onClick={() => {
                  const current = settings.monitored_bookmakers;
                  const updated = current.includes(bk)
                    ? current.filter((b) => b !== bk)
                    : [...current, bk];
                  setSettings({ ...settings, monitored_bookmakers: updated });
                }}
                className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                  settings.monitored_bookmakers.includes(bk)
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : 'bg-gray-800 text-gray-400 border border-gray-700'
                }`}
              >
                {bk.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Markets */}
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
          <h3 className="text-white font-medium mb-3">Monitored Markets</h3>
          <div className="flex flex-wrap gap-2">
            {ALL_MARKETS.map((m) => (
              <button
                key={m}
                onClick={() => {
                  const current = settings.monitored_markets;
                  const updated = current.includes(m)
                    ? current.filter((x) => x !== m)
                    : [...current, m];
                  setSettings({ ...settings, monitored_markets: updated });
                }}
                className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                  settings.monitored_markets.includes(m)
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : 'bg-gray-800 text-gray-400 border border-gray-700'
                }`}
              >
                {m.replace(/_/g, ' ').toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Formats */}
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
          <h3 className="text-white font-medium mb-3">Match Formats</h3>
          <div className="flex gap-2">
            {ALL_FORMATS.map((f) => (
              <button
                key={f}
                onClick={() => {
                  const current = settings.monitored_formats;
                  const updated = current.includes(f)
                    ? current.filter((x) => x !== f)
                    : [...current, f];
                  setSettings({ ...settings, monitored_formats: updated });
                }}
                className={`px-4 py-2 rounded-lg text-sm transition-colors ${
                  settings.monitored_formats.includes(f)
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : 'bg-gray-800 text-gray-400 border border-gray-700'
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* Notification toggles */}
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
          <h3 className="text-white font-medium mb-3">Notifications</h3>
          <div className="space-y-3">
            {[
              { key: 'telegram_alerts', label: 'Telegram Alerts' },
              { key: 'web_push_alerts', label: 'Web Push Notifications' },
              { key: 'sound_alerts', label: 'Sound Alerts' },
            ].map(({ key, label }) => (
              <label key={key} className="flex items-center justify-between">
                <span className="text-gray-300">{label}</span>
                <button
                  onClick={() =>
                    setSettings({ ...settings, [key]: !settings[key as keyof ArbSettings] })
                  }
                  className={`w-11 h-6 rounded-full transition-colors ${
                    settings[key as keyof ArbSettings]
                      ? 'bg-emerald-500'
                      : 'bg-gray-700'
                  }`}
                >
                  <div
                    className={`w-5 h-5 bg-white rounded-full transition-transform ${
                      settings[key as keyof ArbSettings]
                        ? 'translate-x-5'
                        : 'translate-x-0.5'
                    }`}
                  />
                </button>
              </label>
            ))}
          </div>
        </div>

        <button
          onClick={save}
          className="w-full bg-emerald-500 hover:bg-emerald-600 text-white font-medium py-3 rounded-xl transition-colors"
        >
          Save Settings
        </button>
      </div>
    </div>
  );
}
