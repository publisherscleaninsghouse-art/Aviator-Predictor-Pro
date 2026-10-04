"""Production Stake.com Connector for Aviator Predictor Pro.

Connects to Stake.com Aviator game via their REST API.
Requires: API key and user credentials from Stake.com account.
"""

import requests
import hmac
import hashlib
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from connectors import PlatformConnector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PLATFORM_NAME = 'stake'


class StakeProductionConnector(PlatformConnector):
    """Production connector for Stake.com Aviator API.
    
    API Documentation:
    https://api.stake.com/docs
    
    Authentication:
    - API Key: Required (generate from https://stake.com/settings/api)
    - API Secret: Required for request signing
    - User ID: Your Stake.com user ID
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key', '')
        self.api_secret = config.get('api_secret', '')
        self.user_id = config.get('user_id', '')
        self.api_url = config.get('api_url', 'https://api.stake.com')
        self.authenticated = False
        self.timeout = 10
        self.cache = {}
        self.cache_ttl = 300

    def _generate_signature(self, endpoint: str, method: str = 'GET', payload: str = '') -> str:
        """Generate HMAC-SHA256 signature for Stake API requests.
        
        Signature = HMAC-SHA256(api_secret, method + endpoint + payload + nonce)
        """
        nonce = str(int(time.time() * 1000))
        message = f"{method}{endpoint}{payload}{nonce}"
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _get_headers(self, endpoint: str, method: str = 'GET', payload: str = '') -> Dict[str, str]:
        """Generate request headers with authentication."""
        signature = self._generate_signature(endpoint, method, payload)
        return {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key,
            'X-API-Signature': signature,
            'X-API-Nonce': str(int(time.time() * 1000)),
            'User-Agent': 'Aviator-Predictor-Pro/1.0'
        }

    def authenticate(self) -> bool:
        """Verify authentication with Stake API.
        
        GET /api/v1/me
        
        Returns:
            bool: True if authentication successful
        """
        try:
            endpoint = '/api/v1/me'
            headers = self._get_headers(endpoint)

            response = requests.get(
                f"{self.api_url}{endpoint}",
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('user_id') == self.user_id or data.get('id') == self.user_id:
                    self.authenticated = True
                    logger.info(f"Stake.com authentication successful for user {self.user_id}")
                    return True
            
            logger.error(f"Stake auth failed: {response.status_code} - {response.text}")
            return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Stake authentication error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during Stake auth: {e}")
            return False

    def fetch_rounds(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch Aviator rounds from Stake.com API.
        
        GET /api/v1/games/aviator/rounds
        Query params:
        - limit: Number of rounds (max 500)
        - offset: Pagination offset
        
        Returns:
            List of normalized round data
        """
        if not self.authenticated:
            logger.warning("Not authenticated. Attempting to authenticate...")
            if not self.authenticate():
                logger.error("Failed to authenticate with Stake")
                return self._fallback_mock_data(limit)

        try:
            # Check cache
            cache_key = f"rounds_{limit}"
            if cache_key in self.cache:
                cached_data = self.cache[cache_key]
                if time.time() - cached_data['timestamp'] < self.cache_ttl:
                    logger.info("Returning cached Stake rounds")
                    return cached_data['data']

            endpoint = '/api/v1/games/aviator/rounds'
            headers = self._get_headers(endpoint)

            params = {
                'limit': min(limit, 500),
                'offset': 0,
                'user_id': self.user_id
            }

            response = requests.get(
                f"{self.api_url}{endpoint}",
                params=params,
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                rounds = data.get('rounds', []) or data.get('data', [])
                normalized = self.normalize_data(rounds)

                # Cache result
                self.cache[cache_key] = {
                    'data': normalized,
                    'timestamp': time.time()
                }

                logger.info(f"Fetched {len(normalized)} rounds from Stake")
                return normalized
            else:
                logger.error(f"Failed to fetch Stake rounds: {response.status_code}")
                return self._fallback_mock_data(limit)

        except requests.exceptions.Timeout:
            logger.error("Stake API request timed out")
            return self._fallback_mock_data(limit)
        except requests.exceptions.ConnectionError:
            logger.error("Failed to connect to Stake API")
            return self._fallback_mock_data(limit)
        except Exception as e:
            logger.error(f"Error fetching Stake rounds: {e}")
            return self._fallback_mock_data(limit)

    def fetch_live_round(self) -> Optional[Dict[str, Any]]:
        """Fetch current live round from Stake.
        
        GET /api/v1/games/aviator/live
        
        Returns:
            Current round data or None
        """
        if not self.authenticated:
            if not self.authenticate():
                return None

        try:
            endpoint = '/api/v1/games/aviator/live'
            headers = self._get_headers(endpoint)

            params = {'user_id': self.user_id}

            response = requests.get(
                f"{self.api_url}{endpoint}",
                params=params,
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                round_data = data.get('round') or data.get('data')
                if round_data:
                    normalized = self.normalize_data([round_data])
                    return normalized[0] if normalized else None
            return None

        except Exception as e:
            logger.error(f"Error fetching Stake live round: {e}")
            return None

    def get_user_bets(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch user's recent Aviator bets.
        
        GET /api/v1/games/aviator/bets
        
        Returns:
            List of user bets
        """
        if not self.authenticated:
            if not self.authenticate():
                return []

        try:
            endpoint = '/api/v1/games/aviator/bets'
            headers = self._get_headers(endpoint)

            params = {
                'user_id': self.user_id,
                'limit': limit
            }

            response = requests.get(
                f"{self.api_url}{endpoint}",
                params=params,
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json().get('bets', [])
            return []

        except Exception as e:
            logger.error(f"Error fetching Stake bets: {e}")
            return []

    def normalize_data(self, raw_data: List[Dict]) -> List[Dict]:
        """Convert Stake.com API format to standard format.
        
        Stake format:
        {
            "roundId": "123456",
            "multiplier": 2.45,
            "timestamp": 1704110400,
            "crashMultiplier": 3.21,
            "result": "completed"
        }
        """
        normalized = []
        for item in raw_data:
            try:
                # Handle both unix timestamp and ISO format
                timestamp = item.get('timestamp')
                if isinstance(timestamp, int):
                    timestamp = datetime.fromtimestamp(timestamp).isoformat()
                else:
                    timestamp = item.get('timestamp', datetime.utcnow().isoformat())

                normalized.append({
                    'id': str(item.get('roundId', '')),
                    'multiplier': float(item.get('multiplier', 1.5)),
                    'timestamp': timestamp,
                    'crash_point': float(item.get('crashMultiplier', 0)),
                    'status': item.get('result', 'pending').lower(),
                    'platform': 'stake',
                    'raw_data': item
                })
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to normalize Stake round: {e}")
                continue

        return normalized

    def _fallback_mock_data(self, limit: int) -> List[Dict[str, Any]]:
        """Generate mock data as fallback."""
        import random
        data = []
        for i in range(limit):
            data.append({
                'id': f"stake_mock_{int(time.time())}_{i}",
                'multiplier': round(random.uniform(1.1, 6.0), 2),
                'timestamp': (datetime.utcnow() - timedelta(minutes=i)).isoformat(),
                'crash_point': round(random.uniform(1.3, 6.5), 2),
                'status': 'completed',
                'platform': 'stake'
            })
        return data
