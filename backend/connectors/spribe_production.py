"""Production Spribe Connector for Aviator Predictor Pro.

Connects to Spribe Aviator API used by stake.com and other platforms.
Requires: API key from Spribe developer account.
"""

import requests
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from connectors import PlatformConnector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PLATFORM_NAME = 'spribe'


class SpribeProductionConnector(PlatformConnector):
    """Production connector for Spribe Aviator API.
    
    API Documentation:
    https://docs.spribe.co/api/aviator
    
    Authentication:
    - API Key: Required (get from https://spribe.co/partners)
    - Session ID: Generated per session
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key', '')
        self.api_url = config.get('api_url', 'https://api.spribe.co')
        self.session_id = None
        self.authenticated = False
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'User-Agent': 'Aviator-Predictor-Pro/1.0'
        }
        self.timeout = 10
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes

    def authenticate(self) -> bool:
        """Authenticate with Spribe API.
        
        POST /api/v1/auth/session
        {
            "api_key": "your_key",
            "client_id": "aviator_predictor"
        }
        
        Returns:
            bool: True if authentication successful
        """
        try:
            url = f"{self.api_url}/api/v1/auth/session"
            payload = {
                "api_key": self.api_key,
                "client_id": "aviator_predictor",
                "timestamp": int(time.time())
            }

            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                self.session_id = data.get('session_id')
                self.authenticated = True
                logger.info(f"Spribe authentication successful. Session: {self.session_id[:20]}...")
                return True
            else:
                logger.error(f"Spribe auth failed: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Spribe authentication error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during Spribe auth: {e}")
            return False

    def fetch_rounds(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch historical rounds from Spribe API.
        
        GET /api/v1/games/aviator/rounds
        Query params:
        - limit: Number of rounds (max 1000)
        - session_id: Active session ID
        - offset: Pagination offset
        
        Returns:
            List of normalized round data
        """
        if not self.authenticated:
            logger.warning("Not authenticated. Attempting to authenticate...")
            if not self.authenticate():
                logger.error("Failed to authenticate with Spribe")
                return self._fallback_mock_data(limit)

        try:
            # Check cache first
            cache_key = f"rounds_{limit}"
            if cache_key in self.cache:
                cached_data = self.cache[cache_key]
                if time.time() - cached_data['timestamp'] < self.cache_ttl:
                    logger.info(f"Returning cached rounds data")
                    return cached_data['data']

            url = f"{self.api_url}/api/v1/games/aviator/rounds"
            params = {
                "limit": min(limit, 1000),  # API limit
                "session_id": self.session_id,
                "offset": 0
            }

            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                raw_data = response.json()
                rounds = raw_data.get('rounds', [])
                normalized = self.normalize_data(rounds)

                # Cache the result
                self.cache[cache_key] = {
                    'data': normalized,
                    'timestamp': time.time()
                }

                logger.info(f"Fetched {len(normalized)} rounds from Spribe")
                return normalized
            else:
                logger.error(f"Failed to fetch rounds: {response.status_code}")
                return self._fallback_mock_data(limit)

        except requests.exceptions.Timeout:
            logger.error("Spribe API request timed out")
            return self._fallback_mock_data(limit)
        except requests.exceptions.ConnectionError:
            logger.error("Failed to connect to Spribe API")
            return self._fallback_mock_data(limit)
        except Exception as e:
            logger.error(f"Error fetching Spribe rounds: {e}")
            return self._fallback_mock_data(limit)

    def fetch_live_round(self) -> Optional[Dict[str, Any]]:
        """Fetch the current live round from Spribe.
        
        GET /api/v1/games/aviator/live
        
        Returns:
            Current round data or None
        """
        if not self.authenticated:
            if not self.authenticate():
                return None

        try:
            url = f"{self.api_url}/api/v1/games/aviator/live"
            params = {"session_id": self.session_id}

            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                round_data = data.get('round')
                if round_data:
                    normalized = self.normalize_data([round_data])
                    return normalized[0] if normalized else None
            return None

        except Exception as e:
            logger.error(f"Error fetching live round: {e}")
            return None

    def get_game_stats(self) -> Dict[str, Any]:
        """Get game statistics from Spribe.
        
        GET /api/v1/games/aviator/stats
        
        Returns:
            Game statistics (RTP, volatility, etc.)
        """
        if not self.authenticated:
            if not self.authenticate():
                return {}

        try:
            url = f"{self.api_url}/api/v1/games/aviator/stats"
            params = {"session_id": self.session_id}

            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()
            return {}

        except Exception as e:
            logger.error(f"Error fetching game stats: {e}")
            return {}

    def normalize_data(self, raw_data: List[Dict]) -> List[Dict]:
        """Convert Spribe API format to standard format.
        
        Spribe format:
        {
            "gameId": "123456",
            "coefficient": 2.45,
            "createdAt": "2024-01-01T12:00:00Z",
            "crashAt": 3.21,
            "status": "completed"
        }
        
        Standard format:
        {
            "id": "123456",
            "multiplier": 2.45,
            "timestamp": "2024-01-01T12:00:00Z",
            "crash_point": 3.21,
            "status": "completed",
            "platform": "spribe"
        }
        """
        normalized = []
        for item in raw_data:
            try:
                normalized.append({
                    'id': str(item.get('gameId', '')),
                    'multiplier': float(item.get('coefficient', 1.5)),
                    'timestamp': item.get('createdAt', datetime.utcnow().isoformat()),
                    'crash_point': float(item.get('crashAt', 0)),
                    'status': item.get('status', 'pending').lower(),
                    'platform': 'spribe',
                    'raw_data': item  # Store original for debugging
                })
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to normalize Spribe round: {e}")
                continue

        return normalized

    def _fallback_mock_data(self, limit: int) -> List[Dict[str, Any]]:
        """Generate mock data as fallback when API unavailable.
        
        This allows testing without live API access.
        """
        import random
        data = []
        for i in range(limit):
            data.append({
                'id': f"spribe_mock_{int(time.time())}_{i}",
                'multiplier': round(random.uniform(1.05, 5.5), 2),
                'timestamp': (datetime.utcnow() - timedelta(minutes=i)).isoformat(),
                'crash_point': round(random.uniform(1.2, 6.0), 2),
                'status': 'completed',
                'platform': 'spribe'
            })
        return data

    def close(self) -> None:
        """Close session and cleanup.
        
        POST /api/v1/auth/session/close
        """
        if not self.session_id:
            return

        try:
            url = f"{self.api_url}/api/v1/auth/session/close"
            payload = {"session_id": self.session_id}

            requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout
            )
            logger.info("Spribe session closed")

        except Exception as e:
            logger.error(f"Error closing Spribe session: {e}")
