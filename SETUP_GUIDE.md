"""Integration Setup Guide - Step by Step

This document provides detailed step-by-step instructions for integrating
Aviator Predictor Pro with real Aviator game platforms.

## Table of Contents

1. Prerequisites
2. Spribe Integration (stake.com and other platforms)
3. Stake.com Direct Integration
4. Ganymed_Hack Integration
5. Custom Platform Integration
6. Testing and Validation
7. Production Deployment
8. Troubleshooting

---

## 1. Prerequisites

### System Requirements
- Python 3.8+
- Node.js 16+
- SQLite3
- Git
- A compatible API key from your chosen platform

### Installation

```bash
# Clone the repository
git clone https://github.com/publisherscleaninsghouse-art/Aviator-Predictor-Pro.git
cd Aviator-Predictor-Pro

# Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate  # or: .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install
```

---

## 2. Spribe Integration (stake.com, etc.)

### Step 2.1: Get Spribe API Key

1. Visit https://spribe.co/en/partners
2. Click "Create Account" or sign in
3. Go to "Developer Dashboard"
4. Navigate to "API Keys"
5. Click "Generate New Key"
6. Copy your API Key and keep it safe

### Step 2.2: Configure Backend

Edit `backend/app.py` and add configuration:

```python
from connectors.spribe_production import SpribeProductionConnector
from multi_platform import MultiPlatformDataService
from plugin_manager import PluginManager

# Initialize plugin manager
plugin_manager = PluginManager()
plugin_manager.load_all_plugins()

# Initialize multi-platform service
data_service = MultiPlatformDataService()

# Spribe configuration
SPRIBE_CONFIG = {
    'api_key': 'YOUR_SPRIBE_API_KEY_HERE',  # Replace with real key
    'api_url': 'https://api.spribe.co'
}

# Switch to Spribe platform on startup
data_service.switch_platform('spribe', SPRIBE_CONFIG)
```

### Step 2.3: Test Connection

```bash
cd backend
python -c "
from connectors.spribe_production import SpribeProductionConnector

config = {
    'api_key': 'YOUR_API_KEY',
    'api_url': 'https://api.spribe.co'
}

connector = SpribeProductionConnector(config)
if connector.authenticate():
    print('✓ Spribe authentication successful')
    rounds = connector.fetch_rounds(limit=10)
    print(f'✓ Fetched {len(rounds)} rounds')
else:
    print('✗ Authentication failed')
"
```

### Step 2.4: Run Backend

```bash
python app.py
# Output: Running on http://0.0.0.0:5000
```

### Step 2.5: Test API Endpoints

```bash
# Switch to Spribe
curl -X POST http://localhost:5000/api/switch-platform \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "spribe",
    "config": {
      "api_key": "YOUR_API_KEY",
      "api_url": "https://api.spribe.co"
    }
  }'

# Get rounds
curl http://localhost:5000/api/rounds?limit=50

# Get stats
curl http://localhost:5000/api/stats?platform=spribe&hours=24
```

---

## 3. Stake.com Direct Integration

### Step 3.1: Get Stake.com API Credentials

1. Log in to your Stake.com account
2. Go to Settings → API (or https://stake.com/settings/api)
3. Click "Generate New API Key"
4. Copy:
   - API Key
   - API Secret
   - Your User ID (visible in account settings)

### Step 3.2: Configure Backend

Edit `backend/app.py`:

```python
from connectors.stake_production import StakeProductionConnector

# Stake.com configuration
STAKE_CONFIG = {
    'api_key': 'YOUR_STAKE_API_KEY',
    'api_secret': 'YOUR_STAKE_API_SECRET',
    'user_id': 'YOUR_STAKE_USER_ID',
    'api_url': 'https://api.stake.com'
}

# Switch to Stake on startup
data_service.switch_platform('stake', STAKE_CONFIG)
```

### Step 3.3: Test Stake Connection

```bash
python -c "
from connectors.stake_production import StakeProductionConnector

config = {
    'api_key': 'YOUR_KEY',
    'api_secret': 'YOUR_SECRET',
    'user_id': 'YOUR_USER_ID',
    'api_url': 'https://api.stake.com'
}

connector = StakeProductionConnector(config)
if connector.authenticate():
    print('✓ Stake authentication successful')
    rounds = connector.fetch_rounds(limit=10)
    print(f'✓ Fetched {len(rounds)} rounds')
else:
    print('✗ Authentication failed')
"
```

### Step 3.4: Fetch Bets (Optional)

Stake connector also supports fetching user bets:

```python
bets = connector.get_user_bets(limit=50)
for bet in bets:
    print(f"Bet: {bet['id']} - Multiplier: {bet['multiplier']} - Result: {bet['result']}")
```

---

## 4. Ganymed_Hack Integration

### Step 4.1: Get Ganymed API Access

1. Contact Ganymed support or developer team
2. Request API documentation
3. Generate API key from your account
4. Note the API endpoint URL

### Step 4.2: Configure Backend

Edit `backend/app.py`:

```python
from connectors import registry
from connectors import GanymedConnector

# Ganymed configuration
GANYMED_CONFIG = {
    'api_key': 'YOUR_GANYMED_API_KEY',
    'api_url': 'https://ganymed.hack'  # or your endpoint
}

# Switch to Ganymed
data_service.switch_platform('ganymed', GANYMED_CONFIG)
```

---

## 5. Custom Platform Integration

### Step 5.1: Create Plugin Directory

```bash
mkdir -p plugins/my_platform
cd plugins/my_platform
touch __init__.py
touch connector.py
```

### Step 5.2: Implement Connector

**plugins/my_platform/connector.py:**

```python
import requests
from datetime import datetime, timedelta
from connectors import PlatformConnector
import logging

logger = logging.getLogger(__name__)
PLATFORM_NAME = 'my_platform'

class MyPlatformConnector(PlatformConnector):
    """Custom connector for My Aviator Platform."""

    def __init__(self, config):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.api_url = config.get('api_url')
        self.authenticated = False
        self.timeout = 10

    def authenticate(self) -> bool:
        """Authenticate with your platform."""
        try:
            # TODO: Implement authentication
            # Example:
            # response = requests.post(
            #     f"{self.api_url}/auth",
            #     json={'api_key': self.api_key},
            #     timeout=self.timeout
            # )
            # if response.status_code == 200:
            #     self.authenticated = True
            #     return True
            
            if self.api_key:
                self.authenticated = True
                return True
            return False
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False

    def fetch_rounds(self, limit: int = 100):
        """Fetch rounds from your platform API."""
        if not self.authenticated:
            if not self.authenticate():
                return []

        try:
            # TODO: Implement API call to your platform
            # Example:
            # response = requests.get(
            #     f"{self.api_url}/api/rounds",
            #     params={'limit': limit},
            #     headers={'Authorization': f'Bearer {self.api_key}'},
            #     timeout=self.timeout
            # )
            # rounds = response.json().get('rounds', [])
            # return self.normalize_data(rounds)
            
            return []
        except Exception as e:
            logger.error(f"Failed to fetch rounds: {e}")
            return []

    def fetch_live_round(self):
        """Fetch current live round."""
        rounds = self.fetch_rounds(limit=1)
        return rounds[0] if rounds else None

    def normalize_data(self, raw_data):
        """Convert your API format to standard format."""
        normalized = []
        for item in raw_data:
            try:
                normalized.append({
                    'id': str(item.get('id', '')),
                    'multiplier': float(item.get('multiplier', 1.5)),
                    'timestamp': item.get('timestamp', datetime.utcnow().isoformat()),
                    'crash_point': float(item.get('crash_point', 0)),
                    'status': item.get('status', 'completed'),
                    'platform': 'my_platform'
                })
            except Exception as e:
                logger.warning(f"Failed to normalize round: {e}")
                continue
        return normalized
```

### Step 5.3: Load Custom Plugin

The plugin will auto-load on backend startup if placed in `plugins/` directory.

Verify loading:

```bash
python -c "
from plugin_manager import PluginManager
from connectors import registry

pm = PluginManager()
pm.load_all_plugins()

print('Available platforms:', registry.list_platforms())
"
```

---

## 6. Testing and Validation

### Test 1: Connection Test

```bash
curl -X GET http://localhost:5000/api/health
# Response: {"status": "ok", "time": "2024-01-01T12:00:00Z"}
```

### Test 2: Data Fetch Test

```bash
curl -X GET http://localhost:5000/api/rounds?limit=10
# Should return array of rounds
```

### Test 3: Prediction Test

```bash
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "rounds": 100,
    "risk": "medium",
    "target": 2.5,
    "window": "last_24h"
  }'
```

### Test 4: Frontend Connection Test

```bash
cd frontend
npm run dev
# Visit http://localhost:5173
# Check browser console for connection status
```

---

## 7. Production Deployment

### Step 7.1: Environment Configuration

Create `.env` file in backend:

```bash
FLASK_ENV=production
FLASK_DEBUG=False
DATABASE_URL=sqlite:///data/aviator.db
PLUGINS_DIR=plugins

# Spribe
SPRIBE_API_KEY=your_key_here
SPRIBE_API_URL=https://api.spribe.co

# Stake
STAKE_API_KEY=your_key_here
STAKE_API_SECRET=your_secret_here
STAKE_USER_ID=your_user_id
STAKE_API_URL=https://api.stake.com
```

### Step 7.2: Update app.py for Environment Variables

```python
import os
from dotenv import load_dotenv

load_dotenv()

SPRIBE_CONFIG = {
    'api_key': os.getenv('SPRIBE_API_KEY'),
    'api_url': os.getenv('SPRIBE_API_URL')
}

STAKE_CONFIG = {
    'api_key': os.getenv('STAKE_API_KEY'),
    'api_secret': os.getenv('STAKE_API_SECRET'),
    'user_id': os.getenv('STAKE_USER_ID'),
    'api_url': os.getenv('STAKE_API_URL')
}
```

### Step 7.3: Production Deployment

#### Using Gunicorn

```bash
pip install gunicorn
gunicorn --workers 4 --bind 0.0.0.0:5000 app:app
```

#### Using Docker

**Dockerfile:**

```dockerfile
FROM python:3.9
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

```bash
docker build -t aviator-predictor .
docker run -p 5000:5000 -e SPRIBE_API_KEY=your_key aviator-predictor
```

---

## 8. Troubleshooting

### Issue: "Authentication Failed"

**Causes:**
- Invalid API key
- Wrong API endpoint
- API account permissions issue

**Solutions:**
1. Verify API key is correct
2. Check endpoint URL
3. Test with platform's official documentation
4. Check rate limiting (may be temporarily blocked)

**Debug:**
```python
from connectors.spribe_production import SpribeProductionConnector
connector = SpribeProductionConnector(config)
result = connector.authenticate()
print(f"Auth result: {result}")
print(f"Session: {connector.session_id}")
```

### Issue: "No Data Returned"

**Causes:**
- Platform has no active games
- Data format changed
- API response parsing error

**Solutions:**
1. Check if platform has active games
2. Add logging to see raw API response:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

rounds = connector.fetch_rounds(limit=10)
print(f"Rounds: {rounds}")
```

3. Check normalize_data() output

### Issue: "Connection Timeout"

**Causes:**
- API endpoint unreachable
- Network issues
- API rate limiting

**Solutions:**
1. Check internet connection
2. Verify API endpoint URL
3. Increase timeout value
4. Implement retry logic

```python
from connectors.spribe_production import SpribeProductionConnector
connector = SpribeProductionConnector(config)
connector.timeout = 30  # Increase from default 10
```

### Issue: "Plugin Not Loading"

**Solutions:**
1. Verify plugin directory structure
2. Ensure connector.py has PLATFORM_NAME
3. Check Python logs for errors

```bash
python -c "from plugin_manager import PluginManager; pm = PluginManager(); pm.load_all_plugins()"
```

---

## Summary

✅ You now have:
1. Multi-platform connector architecture
2. Production Spribe connector (stake.com)
3. Production Stake.com connector
4. Plugin system for custom platforms
5. Complete integration documentation

Next steps:
1. Choose your platform (Spribe, Stake, or custom)
2. Get API credentials
3. Configure backend
4. Test connections
5. Deploy to production

## Support

For issues:
1. Check logs: `tail -f backend/logs/app.log`
2. Review INTEGRATION_GUIDE.md
3. Test connectors independently
4. Check platform API documentation
"""
