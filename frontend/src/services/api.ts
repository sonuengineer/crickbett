import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const res = await axios.post('/api/v1/auth/refresh', {
            refresh_token: refreshToken,
          });
          localStorage.setItem('access_token', res.data.access_token);
          localStorage.setItem('refresh_token', res.data.refresh_token);
          error.config.headers.Authorization = `Bearer ${res.data.access_token}`;
          return api.request(error.config);
        } catch {
          localStorage.clear();
          window.location.href = '/login';
        }
      } else {
        localStorage.clear();
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Auth
export const login = (email: string, password: string) =>
  api.post('/auth/login', { email, password });

export const register = (data: { email: string; username: string; password: string }) =>
  api.post('/auth/register', data);

// Matches
export const getMatches = (params?: { status?: string; format?: string }) =>
  api.get('/cricket/matches/', { params });

export const getLiveMatches = () => api.get('/cricket/matches/live');

// Odds
export const getMatchOdds = (matchId: string, marketType?: string) =>
  api.get(`/cricket/odds/${matchId}`, { params: { market_type: marketType } });

export const getOddsComparison = (matchId: string, marketType = 'match_winner') =>
  api.get(`/cricket/odds/${matchId}/comparison`, { params: { market_type: marketType } });

// Arbs
export const getActiveArbs = (params?: { arb_type?: string; min_profit?: number }) =>
  api.get('/cricket/arb/active', { params });

export const getArbHistory = (params?: { arb_type?: string; limit?: number }) =>
  api.get('/cricket/arb/history', { params });

export const dismissArb = (arbId: string) => api.post(`/cricket/arb/${arbId}/dismiss`);

// Positions
export const getPositions = () => api.get('/cricket/positions/');

export const createPosition = (data: {
  match_id: string;
  market_type: string;
  initial_bet_bookmaker: string;
  initial_bet_selection: string;
  initial_bet_odds: number;
  initial_bet_stake: number;
}) => api.post('/cricket/positions/', data);

export const recordHedge = (positionId: string, data: {
  hedge_bet_bookmaker: string;
  hedge_bet_selection: string;
  hedge_bet_odds: number;
  hedge_bet_stake: number;
}) => api.put(`/cricket/positions/${positionId}/hedge`, data);

export const closePosition = (positionId: string) =>
  api.put(`/cricket/positions/${positionId}/close`);

// Settings
export const getArbSettings = () => api.get('/cricket/settings/');

export const updateArbSettings = (data: Record<string, unknown>) =>
  api.put('/cricket/settings/', data);

// Hedge Monitor
export const createHedgeMonitor = (data: {
  match_team_a: string;
  match_team_b: string;
  tournament?: string;
  bookmaker: string;
  selection: string;
  odds: number;
  stake: number;
  market_type?: string;
}) => api.post('/cricket/hedge-monitor/', data);

export const getHedgeMonitors = () => api.get('/cricket/hedge-monitor/');

export const getHedgeMonitor = (id: string) =>
  api.get(`/cricket/hedge-monitor/${id}`);

export const markHedged = (id: string) =>
  api.post(`/cricket/hedge-monitor/${id}/hedged`);

export const deleteHedgeMonitor = (id: string) =>
  api.delete(`/cricket/hedge-monitor/${id}`);

// Capture (from extension / manual)
export const captureOdds = (data: {
  match_team_a: string;
  match_team_b: string;
  bookmaker: string;
  market_type?: string;
  odds: { selection: string; odds_decimal: number; is_live?: boolean }[];
}) => api.post('/cricket/capture/', data);

export default api;
