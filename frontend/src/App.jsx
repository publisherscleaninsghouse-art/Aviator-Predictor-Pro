import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { io } from 'socket.io-client';

const socket = io('http://localhost:5000', { transports: ['websocket'] });

function App() {
  const [dashboard, setDashboard] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    rounds: 150,
    risk: 'medium',
    target: 2.3,
    window: 'last_24h',
  });

  useEffect(() => {
    const loadData = async () => {
      try {
        const [dashboardRes, leaderboardRes, analyticsRes] = await Promise.all([
          axios.get('/api/dashboard'),
          axios.get('/api/leaderboard'),
          axios.get('/api/analytics'),
        ]);

        setDashboard(dashboardRes.data);
        setLeaderboard(leaderboardRes.data);
        setAnalytics(analyticsRes.data);
      } catch (error) {
        console.error('Failed to load app data:', error);
      }
    };

    loadData();

    socket.on('connect', () => console.log('Socket connected'));
    socket.on('stats_update', (payload) => {
      setDashboard((prev) =>
        prev
          ? {
              ...prev,
              metrics: {
                ...prev.metrics,
                trend: payload.trend || prev.metrics.trend,
                confidence: payload.confidence || prev.metrics.confidence,
                risk: payload.risk || prev.metrics.risk,
              },
            }
          : prev
      );
    });

    return () => {
      socket.off('stats_update');
      socket.disconnect();
    };
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handlePredict = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post('/api/predict', {
        rounds: Number(form.rounds),
        risk: form.risk,
        target: Number(form.target),
        window: form.window,
      });

      setPrediction(response.data.prediction);
      setDashboard((prev) => ({
        ...prev,
        chart: response.data.chart,
      }));
    } catch (error) {
      console.error('Prediction failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const metricCards = useMemo(() => {
    if (!dashboard) return [];

    return [
      { title: 'Trend Analysis', value: `${dashboard.metrics.trend}%`, unit: 'Current trend', icon: '📈', color: '#6ee7b7' },
      { title: 'Prediction Confidence', value: `${dashboard.metrics.confidence}%`, unit: 'Accuracy score', icon: '🎯', color: '#7dd3fc' },
      { title: 'Risk Assessment', value: dashboard.metrics.risk, unit: 'Live level', icon: '⚠️', color: '#f59e0b' },
      { title: 'Win Rate', value: `${dashboard.metrics.winRate}%`, unit: 'Historical avg', icon: '🏆', color: '#a78bfa' },
    ];
  }, [dashboard]);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-icon">✈️</span>
          <span>Aviator Predictor Pro</span>
        </div>

        <nav className="nav">
          <button className="nav-btn active">Dashboard</button>
          <button className="nav-btn">Analytics</button>
          <button className="nav-btn">Reports</button>
          <button className="nav-btn">Settings</button>
        </nav>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div>
            <h1>Live Analytics Dashboard</h1>
            <p>Advanced Aviator performance monitoring</p>
          </div>
          <div className="status-pill">
            <span className="status-dot" /> Live
          </div>
        </header>

        <section className="metric-grid">
          {metricCards.map((card) => (
            <div key={card.title} className="metric-card">
              <div className="metric-header">
                <span>{card.icon}</span>
                <h3>{card.title}</h3>
              </div>
              <div className="metric-value" style={{ color: card.color }}>{card.value}</div>
              <div className="metric-unit">{card.unit}</div>
            </div>
          ))}
        </section>

        <section className="content-grid">
          <div className="panel chart-panel">
            <h2>Multiplier Trend</h2>
            {dashboard && (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={dashboard.chart}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                  <XAxis dataKey="time" stroke="#b9c3d6" />
                  <YAxis stroke="#b9c3d6" domain={[0, 6]} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="multiplier" stroke="#7dd3fc" name="Actual" strokeWidth={2} dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="prediction" stroke="#6ee7b7" name="Forecast" strokeDasharray="6 6" strokeWidth={2} dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="panel side-panel">
            <h2>Prediction Engine</h2>
            <form onSubmit={handlePredict} className="prediction-form">
              <label>
                Historical rounds
                <input type="number" name="rounds" value={form.rounds} onChange={handleChange} />
              </label>

              <label>
                Risk tolerance
                <select name="risk" value={form.risk} onChange={handleChange}>
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </label>

              <label>
                Target multiplier
                <input type="number" step="0.1" name="target" value={form.target} onChange={handleChange} />
              </label>

              <label>
                Analysis window
                <select name="window" value={form.window} onChange={handleChange}>
                  <option value="last_1h">Last 1 hour</option>
                  <option value="last_6h">Last 6 hours</option>
                  <option value="last_24h">Last 24 hours</option>
                  <option value="last_7d">Last 7 days</option>
                </select>
              </label>

              <button type="submit" disabled={loading}>
                {loading ? 'Analyzing...' : 'Run Prediction'}
              </button>
            </form>

            {prediction && (
              <div className="prediction-result">
                <div className="result-row">
                  <span>Forecast</span>
                  <strong>{prediction.predicted}x</strong>
                </div>
                <div className="result-row">
                  <span>Confidence</span>
                  <strong>{prediction.confidence}%</strong>
                </div>
                <div className="result-row">
                  <span>Risk</span>
                  <strong>{prediction.risk_score}</strong>
                </div>
                <div className={`result-row recommendation ${prediction.recommendation.toLowerCase()}`}>
                  <span>Recommendation</span>
                  <strong>{prediction.recommendation}</strong>
                </div>
              </div>
            )}
          </div>
        </section>

        <section className="bottom-grid">
          <div className="panel">
            <h2>Leaderboard</h2>
            <div className="leaderboard-list">
              {leaderboard.map((player, index) => (
                <div className="leaderboard-item" key={player.name}>
                  <div className="rank">#{index + 1}</div>
                  <div className="player-name">{player.name}</div>
                  <div className="player-score">{player.score}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="panel">
            <h2>Analytics Summary</h2>
            {analytics && (
              <div className="analytics-list">
                <div><span>Volatility</span><strong>{analytics.volatility}</strong></div>
                <div><span>Average Multiplier</span><strong>{analytics.averageMultiplier}</strong></div>
                <div><span>Win Rate</span><strong>{analytics.winRate}%</strong></div>
                <div><span>Peak Multiplier</span><strong>{analytics.peakMultiplier}</strong></div>
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
