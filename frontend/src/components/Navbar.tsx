import { Link, useLocation } from 'react-router-dom';
import { useArbStore } from '../stores/arbStore';
import { useAuthStore } from '../stores/authStore';

const navItems = [
  { path: '/', label: 'Dashboard' },
  { path: '/hedge', label: 'Hedge Monitor' },
  { path: '/matches', label: 'Live Matches' },
  { path: '/history', label: 'Arb History' },
  { path: '/positions', label: 'Positions' },
  { path: '/settings', label: 'Settings' },
  { path: '/how-to-use', label: 'How To Use' },
];

export default function Navbar() {
  const location = useLocation();
  const { activeArbs, soundEnabled, toggleSound } = useArbStore();
  const { logout } = useAuthStore();

  return (
    <nav className="bg-gray-900 border-b border-gray-800 px-6 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-8">
          <Link to="/" className="text-xl font-bold text-emerald-400">
            CricketArb
          </Link>

          <div className="flex gap-1">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`px-3 py-2 rounded-lg text-sm transition-colors ${
                  location.pathname === item.path
                    ? 'bg-gray-800 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
                }`}
              >
                {item.label}
              </Link>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-4">
          {activeArbs.length > 0 && (
            <span className="bg-emerald-500/20 text-emerald-400 px-3 py-1 rounded-full text-sm font-medium animate-pulse-fast">
              {activeArbs.length} Active Arbs
            </span>
          )}

          <button
            onClick={toggleSound}
            className={`p-2 rounded-lg transition-colors ${
              soundEnabled
                ? 'text-emerald-400 bg-emerald-400/10'
                : 'text-gray-500 bg-gray-800'
            }`}
            title={soundEnabled ? 'Sound ON' : 'Sound OFF'}
          >
            {soundEnabled ? '🔊' : '🔇'}
          </button>

          <button
            onClick={logout}
            className="text-gray-400 hover:text-white text-sm px-3 py-2"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}
