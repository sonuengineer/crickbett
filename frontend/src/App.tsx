import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { useAuth } from './hooks/useAuth';
import { useWebSocket } from './hooks/useWebSocket';
import Layout from './components/Layout';
import SoundAlert from './components/SoundAlert';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import LiveMatches from './pages/LiveMatches';
import ArbHistory from './pages/ArbHistory';
import Positions from './pages/Positions';
import Settings from './pages/Settings';
import HedgeMonitor from './pages/HedgeMonitor';
import HowToUse from './pages/HowToUse';

function AuthenticatedApp() {
  useWebSocket();

  return (
    <>
      <SoundAlert />
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/matches" element={<LiveMatches />} />
          <Route path="/history" element={<ArbHistory />} />
          <Route path="/hedge" element={<HedgeMonitor />} />
          <Route path="/positions" element={<Positions />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/how-to-use" element={<HowToUse />} />
        </Route>
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </>
  );
}

export default function App() {
  const { isAuthenticated } = useAuth();

  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#1f2937',
            color: '#fff',
            border: '1px solid #374151',
          },
        }}
      />
      {isAuthenticated ? (
        <AuthenticatedApp />
      ) : (
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="*" element={<Navigate to="/login" />} />
        </Routes>
      )}
    </BrowserRouter>
  );
}
