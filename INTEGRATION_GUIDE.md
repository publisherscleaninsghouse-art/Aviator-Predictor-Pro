# INTEGRATION GUIDE: Connecting to Aviator Game Platforms

## Overview

The Aviator Predictor Pro is designed to work with **any Aviator-style game** including:
- Spribe Aviator (stake.com, etc.)
- Ganymed_Hack
- Custom platforms

## Built-in Platform Support

### 1. Spribe (stake.com, most platforms)

**Configuration:**
```python
from multi_platform import MultiPlatformDataService

service = MultiPlatformDataService()

config = {
    'api_key': 'YOUR_SPRIBE_API_KEY',
    'api_url': 'https://api.spribe.co'
}

service.switch_platform('spribe', config)
rounds = service.fetch_and_cache_rounds(limit=100)
```

**Getting API Key:**
1. Go to https://spribe.co/en/partners
2. Sign up for developer account
3. Create API credentials
4. Copy your API key

### 2. Stake.com

**Configuration:**
```python
config = {
    'api_key': 'YOUR_STAKE_API_KEY',
    'user_id': 'YOUR_USER_ID',
    'api_url': 'https://api.stake.com'
}

service.switch_platform('stake', config)
```

**Getting API Key:**
1. Log in to stake.com
2. Go to Settings → API
3. Generate API key
4. Note your user ID

### 3. Ganymed_Hack

**Configuration:**
```python
config = {
    'api_key': 'YOUR_GANYMED_API_KEY',
    'api_url': 'https://ganymed.hack'
}

service.switch_platform('ganymed', config)
```

## Adding a Custom Platform

### Step 1: Create Plugin Structure

```
plugins/
  my_platform/
    __init__.py
    connector.py
    config.json
```

### Step 2: Implement Connector

**plugins/my_platform/connector.py:**

```python
from connectors import PlatformConnector
from datetime import datetime, timedelta
import random

PLATFORM_NAME = 'my_platform'

class MyPlatformConnector(PlatformConnector):
    """Custom connector for My Aviator Platform."""

    def __init__(self, config):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.api_url = config.get('api_url')

    def authenticate(self) -> bool:
        """Authenticate with your platform API."""
        try:
            # Implement real authentication here
            # Example: POST /auth with api_key
            if self.api_key:
                return True
            return False
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False

    def fetch_rounds(self, limit: int = 100) -> list:
        """Fetch historical rounds from your platform.
        
        Expected return format (gets normalized):
        [
            {
                'round_id': '12345',
                'value': 2.5,
                'ended_at': '2024-01-01T12:00:00Z',
                'crash': 3.2,
                'result': 'crashed'
            },
            ...
        ]
        """
        try:
            # Implement API call to your platform
            # Example: GET /api/rounds?limit={limit}
            rounds = self._fetch_from_api(limit)
            return self.normalize_data(rounds)
        except Exception as e:
            print(f"Failed to fetch rounds: {e}")
            # Return mock data as fallback
            return self._mock_data(limit)

    def fetch_live_round(self):
        """Fetch current live round."""
        rounds = self.fetch_rounds(limit=1)
        return rounds[0] if rounds else None

    def normalize_data(self, raw_data: list) -> list:
        """Convert your platform's format to standard format."""
        normalized = []
        for item in raw_data:
            normalized.append({
                'id': item.get('round_id'),
                'multiplier': float(item.get('value', 1.5)),
                'timestamp': item.get('ended_at'),
                'crash_point': float(item.get('crash', 0)),
                'status': item.get('result', 'crashed'),
                'platform': 'my_platform'
            })
        return normalized

    def _fetch_from_api(self, limit: int):
        """Implement actual API call to your platform."""
        import requests
        headers = {'Authorization': f'Bearer {self.api_key}'}
        response = requests.get(
            f"{self.api_url}/api/rounds",
            params={'limit': limit},
            headers=headers
        )
        return response.json()

    def _mock_data(self, limit: int):
        """Generate mock data for testing."""
        return [
            {
                'round_id': str(i),
                'value': round(random.uniform(1.1, 5.0), 2),
                'ended_at': (datetime.utcnow() - timedelta(minutes=i)).isoformat(),
                'crash': round(random.uniform(1.5, 5.5), 2),
                'result': 'crashed'
            }
            for i in range(limit)
        ]
```

### Step 3: Load Plugin

**In backend/app.py:**

```python
from plugin_manager import PluginManager
from multi_platform import MultiPlatformDataService

# Initialize plugin manager
plugin_manager = PluginManager()
plugin_manager.load_all_plugins()

# Use your custom platform
service = MultiPlatformDataService()
config = {
    'api_key': 'YOUR_API_KEY',
    'api_url': 'YOUR_PLATFORM_URL'
}
service.switch_platform('my_platform', config)
```

## Integration Example

### Flask API Endpoint

```python
from flask import Flask, jsonify, request
from multi_platform import MultiPlatformDataService

app = Flask(__name__)
service = MultiPlatformDataService()

@app.post('/api/switch-platform')
def switch_platform():
    """Switch to a different platform."""
    data = request.json
    platform = data.get('platform')
    config = data.get('config')
    
    success = service.switch_platform(platform, config)
    
    return jsonify({
        'success': success,
        'platform': platform,
        'available': service.list_available_platforms()
    })

@app.get('/api/rounds')
def get_rounds():
    """Get rounds from active platform."""
    limit = request.args.get('limit', 100, type=int)
    rounds = service.fetch_and_cache_rounds(limit)
    return jsonify(rounds)

@app.get('/api/stats')
def get_stats():
    """Get platform statistics."""
    platform = request.args.get('platform')
    hours = request.args.get('hours', 24, type=int)
    
    if not platform:
        platform = service.active_platform
    
    stats = service.get_platform_stats(platform, hours)
    return jsonify(stats)
```

## Testing Your Integration

### 1. Verify Connection

```python
from multi_platform import MultiPlatformDataService

service = MultiPlatformDataService()
config = {'api_key': 'test_key', 'api_url': 'https://api.example.com'}

if service.switch_platform('my_platform', config):
    print("✓ Connected successfully")
else:
    print("✗ Connection failed")
```

### 2. Fetch Sample Data

```python
rounds = service.fetch_and_cache_rounds(limit=50)
print(f"Fetched {len(rounds)} rounds")
for round_data in rounds[:3]:
    print(round_data)
```

### 3. View Statistics

```python
stats = service.get_platform_stats('my_platform', hours=24)
print(f"Average multiplier: {stats['avg_multiplier']}")
print(f"Volatility: {stats['volatility']}")
```

## API Reference

### PlatformConnector Base Class

```python
class PlatformConnector(ABC):
    def authenticate(self) -> bool
    def fetch_rounds(self, limit: int) -> List[Dict]
    def fetch_live_round(self) -> Optional[Dict]
    def normalize_data(self, raw_data: List[Dict]) -> List[Dict]
```

### MultiPlatformDataService

```python
service = MultiPlatformDataService(db_path="data/aviator.db")

# Platform management
service.switch_platform(platform: str, config: Dict) -> bool
service.list_available_platforms() -> List[str]

# Data fetching
service.fetch_and_cache_rounds(limit: int) -> List[Dict]
service.fetch_live_round() -> Optional[Dict]

# Caching
service.get_cached_rounds(platform: Optional[str], limit: int) -> List[Dict]

# Analytics
service.get_platform_stats(platform: str, hours: int) -> Dict
```

## Common Issues

### Issue: Authentication Failed

**Solution:**
1. Verify API key is correct
2. Check API endpoint URL
3. Ensure API account has required permissions
4. Check rate limiting

### Issue: No Data Returned

**Solution:**
1. Verify platform has active games
2. Check data format in normalize_data()
3. Add logging to debug API response
4. Test with mock data first

### Issue: Plugin Not Loading

**Solution:**
1. Verify plugin directory structure
2. Ensure connector.py contains PlatformConnector subclass
3. Check PLATFORM_NAME is set
4. Review plugin manager logs

## Support

For issues or questions:
1. Check the plugin examples in `plugins/`
2. Review the base connector implementation in `connectors.py`
3. Enable debug logging for troubleshooting

## Next Steps

1. ✅ Choose your platform (Spribe, Stake, Ganymed, or custom)
2. ✅ Configure API credentials
3. ✅ Test connection
4. ✅ Deploy to production
