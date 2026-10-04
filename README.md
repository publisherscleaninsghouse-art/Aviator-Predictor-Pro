# Aviator Predictor Pro - Multi-Platform Architecture

## Project Structure

```
Aviator-Predictor-Pro/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── connectors.py          # Platform connector implementations
│   ├── plugin_manager.py      # Plugin loading system
│   ├── multi_platform.py      # Multi-platform data service
│   ├── requirements.txt
│   └── data/
│       └── aviator.db         # SQLite database
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # Main React component
│   │   └── index.css
│   ├── vite.config.js
│   ├── package.json
│   └── index.html
├── plugins/                   # Custom platform plugins
│   ├── example_plugin/
│   │   ├── __init__.py
│   │   ├── connector.py
│   │   └── config.json
│   └── ...
├── INTEGRATION_GUIDE.md        # Detailed integration instructions
└── README.md
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│          React Frontend Dashboard                    │
│  (Charts, Predictions, Analytics, Leaderboard)      │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│         Flask REST API + WebSocket                   │
│  (Endpoints: /api/predict, /api/rounds, etc)        │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│    Multi-Platform Data Service                       │
│  (Platform switching, caching, normalization)        │
└─────────────────────────────────────────────────────┘
                        ↓
┌──────────┬───────────┬──────────┬─────────┐
│  Spribe  │   Stake   │ Ganymed  │ Custom  │
│Connector │Connector  │Connector │ Plugin  │
└──────────┴───────────┴──────────┴─────────┘
                        ↓
┌──────────┬───────────┬──────────┐
│ Spribe   │ Stake.com │ Ganymed  │
│   API    │    API    │   API    │
└──────────┴───────────┴──────────┘
```

## Supported Platforms

### Built-in
- ✅ **Spribe** - Used by stake.com and other major platforms
- ✅ **Stake.com** - Direct integration
- ✅ **Ganymed_Hack** - Alternative Aviator variant

### Extensible
- 📦 Create custom plugins for any platform
- 🔌 Plugin system loads connectors dynamically
- 🎯 Automatic data normalization

## Key Features

### 1. Multi-Platform Support
- Switch between platforms with single API call
- Unified data format across all platforms
- Platform-specific optimizations

### 2. Plugin System
- Easy integration of new platforms
- No core code modifications needed
- Hot-loading of plugins at startup

### 3. Data Caching
- SQLite database for performance
- Cross-platform data storage
- Historical analytics

### 4. Real-time Updates
- WebSocket support for live data
- Prediction streaming
- Live metrics refresh

### 5. Advanced Analytics
- Volatility calculation
- Pattern recognition
- Risk scoring
- Leaderboard management

## Getting Started

### Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or: .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Configure your platform
# Edit backend/app.py and set your API credentials

python app.py
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open: http://localhost:5173

## Usage Examples

### Switch Platform (REST API)

```bash
curl -X POST http://localhost:5000/api/switch-platform \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "spribe",
    "config": {
      "api_key": "your_key",
      "api_url": "https://api.spribe.co"
    }
  }'
```

### Get Rounds

```bash
curl http://localhost:5000/api/rounds?limit=50&platform=spribe
```

### Get Platform Statistics

```bash
curl http://localhost:5000/api/stats?platform=spribe&hours=24
```

## Creating a Custom Plugin

See `INTEGRATION_GUIDE.md` for detailed instructions.

Quick example:

1. Create `plugins/my_platform/connector.py`
2. Implement `MyPlatformConnector(PlatformConnector)`
3. Set `PLATFORM_NAME = 'my_platform'`
4. Plugin auto-loads at startup

## Configuration

### Environment Variables

```bash
# Backend
FLASK_ENV=production
FLASK_DEBUG=False
DATABASE_URL=sqlite:///data/aviator.db
PLUGINS_DIR=plugins

# Frontend
VITE_API_URL=http://localhost:5000
VITE_WS_URL=ws://localhost:5000
```

## Database Schema

### predictions
```sql
CREATE TABLE predictions (
    id INTEGER PRIMARY KEY,
    name TEXT,
    rounds INTEGER,
    risk TEXT,
    target REAL,
    predicted REAL,
    confidence INTEGER,
    risk_score INTEGER,
    recommendation TEXT,
    created_at TEXT
);
```

### leaderboard
```sql
CREATE TABLE leaderboard (
    id INTEGER PRIMARY KEY,
    name TEXT,
    score REAL,
    confidence INTEGER,
    streak INTEGER,
    pnl REAL,
    updated_at TEXT
);
```

### platform_rounds
```sql
CREATE TABLE platform_rounds (
    id TEXT PRIMARY KEY,
    platform TEXT,
    multiplier REAL,
    crash_point REAL,
    timestamp TEXT,
    status TEXT,
    cached_at TEXT
);
```

## API Endpoints

### Authentication & Platform Management
- `POST /api/switch-platform` - Switch active platform
- `GET /api/platforms` - List available platforms

### Data
- `GET /api/dashboard` - Dashboard metrics
- `GET /api/rounds` - Fetch rounds from active platform
- `GET /api/stats` - Platform statistics

### Predictions
- `POST /api/predict` - Generate prediction
- `GET /api/leaderboard` - Leaderboard data
- `GET /api/analytics` - Advanced analytics

### WebSocket Events
- `stats_update` - Real-time metric updates
- `new_round` - New round notification
- `prediction_result` - Prediction result

## Troubleshooting

### Backend won't start
```bash
# Check Python version (3.8+)
python --version

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check port 5000 is available
netstat -an | grep 5000
```

### Frontend connection issues
```bash
# Check Vite proxy in vite.config.js
# Ensure backend is running on port 5000
# Clear browser cache and restart dev server
```

### Plugin not loading
```bash
# Check plugin directory structure
# Verify connector.py exists
# Check plugin logs in console output
```

## Performance Tips

1. **Caching**: Rounds are cached in SQLite for faster access
2. **Batch Processing**: Fetch multiple rounds in one request
3. **Database Indexing**: Platform column is indexed for queries
4. **WebSocket**: Use for real-time updates instead of polling

## Security Considerations

1. **API Keys**: Store in environment variables, never commit
2. **Authentication**: Implement user auth for production
3. **Rate Limiting**: Add request throttling
4. **CORS**: Configure properly for your domain
5. **SSL/TLS**: Use HTTPS in production

## Contributing

Contributions welcome! Areas:
- New platform connectors
- Improved prediction algorithms
- UI/UX enhancements
- Documentation
- Bug fixes

## License

MIT License - See LICENSE file

## Disclaimer

This tool is for educational and research purposes. Gambling involves risk. Use responsibly and only wager what you can afford to lose.
