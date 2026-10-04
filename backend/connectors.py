"""Aviator Predictor Pro - Multi-Platform API Connector

This module provides universal connectors for various Aviator game platforms.
Supports: Spribe, Stake.com, and extensible for other platforms.
"""

import os
import json
import time
import random
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import sqlite3
from datetime import datetime, timedelta


class PlatformConnector(ABC):
    """Abstract base class for platform-specific connectors."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.platform_name = self.__class__.__name__

    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the platform."""
        pass

    @abstractmethod
    def fetch_rounds(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch historical round data from the platform."""
        pass

    @abstractmethod
    def fetch_live_round(self) -> Optional[Dict[str, Any]]:
        """Fetch the current/latest round data."""
        pass

    def normalize_data(self, raw_data: List[Dict]) -> List[Dict]:
        """Convert platform-specific data to standard format.
        
        Standard format:
        {
            'id': str,
            'multiplier': float,
            'timestamp': str (ISO format),
            'crash_point': float,
            'status': 'crashed' | 'pending'
        }
        """
        return raw_data


class SpribeConnector(PlatformConnector):
    """Connector for Spribe Aviator games."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key', '')
        self.api_url = config.get('api_url', 'https://api.spribe.co')
        self.session_id = None
        self.authenticated = False

    def authenticate(self) -> bool:
        """Authenticate with Spribe API."""
        try:
            # In production, use real API authentication
            if self.api_key:
                self.session_id = f"spribe_{int(time.time())}"
                self.authenticated = True
                return True
            return False
        except Exception as e:
            print(f"Spribe authentication failed: {e}")
            return False

    def fetch_rounds(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch rounds from Spribe API.
        
        In production:
        GET /api/v1/rounds?limit={limit}&session_id={session_id}
        """
        if not self.authenticated:
            return self._mock_spribe_data(limit)

        try:
            # Mock data - replace with real API call
            rounds = self._mock_spribe_data(limit)
            return self.normalize_data(rounds)
        except Exception as e:
            print(f"Failed to fetch Spribe rounds: {e}")
            return self._mock_spribe_data(limit)

    def fetch_live_round(self) -> Optional[Dict[str, Any]]:
        """Fetch current live round from Spribe."""
        rounds = self.fetch_rounds(limit=1)
        return rounds[0] if rounds else None

    def normalize_data(self, raw_data: List[Dict]) -> List[Dict]:
        """Convert Spribe format to standard format."""
        normalized = []
        for item in raw_data:
            normalized.append({
                'id': item.get('gameId', str(random.randint(1000, 9999))),
                'multiplier': float(item.get('coefficient', 1.5)),
                'timestamp': item.get('createdAt', datetime.utcnow().isoformat()),
                'crash_point': float(item.get('crashAt', 0)),
                'status': item.get('status', 'crashed'),
                'platform': 'spribe'
            })
        return normalized

    @staticmethod
    def _mock_spribe_data(limit: int) -> List[Dict[str, Any]]:
        """Generate mock Spribe-formatted data."""
        return [
            {
                'gameId': str(i),
                'coefficient': round(random.uniform(1.1, 4.5), 2),
                'createdAt': (datetime.utcnow() - timedelta(minutes=i)).isoformat(),
                'crashAt': round(random.uniform(1.5, 5.0), 2),
                'status': random.choice(['crashed', 'completed'])
            }
            for i in range(limit)
        ]


class StakeConnector(PlatformConnector):
    """Connector for Stake.com Aviator games."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key', '')
        self.api_url = config.get('api_url', 'https://api.stake.com')
        self.user_id = config.get('user_id', '')
        self.authenticated = False

    def authenticate(self) -> bool:
        """Authenticate with Stake API."""
        try:
            if self.api_key and self.user_id:
                self.authenticated = True
                return True
            return False
        except Exception as e:
            print(f"Stake authentication failed: {e}")
            return False

    def fetch_rounds(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch rounds from Stake API.
        
        In production:
        GET /api/v1/games/aviator/rounds?limit={limit}&user_id={user_id}
        """
        if not self.authenticated:
            return self._mock_stake_data(limit)

        try:
            rounds = self._mock_stake_data(limit)
            return self.normalize_data(rounds)
        except Exception as e:
            print(f"Failed to fetch Stake rounds: {e}")
            return self._mock_stake_data(limit)

    def fetch_live_round(self) -> Optional[Dict[str, Any]]:
        """Fetch current live round from Stake."""
        rounds = self.fetch_rounds(limit=1)
        return rounds[0] if rounds else None

    def normalize_data(self, raw_data: List[Dict]) -> List[Dict]:
        """Convert Stake format to standard format."""
        normalized = []
        for item in raw_data:
            normalized.append({
                'id': item.get('roundId', str(random.randint(10000, 99999))),
                'multiplier': float(item.get('multiplier', 1.8)),
                'timestamp': item.get('timestamp', datetime.utcnow().isoformat()),
                'crash_point': float(item.get('crashMultiplier', 0)),
                'status': item.get('result', 'crashed'),
                'platform': 'stake'
            })
        return normalized

    @staticmethod
    def _mock_stake_data(limit: int) -> List[Dict[str, Any]]:
        """Generate mock Stake-formatted data."""
        return [
            {
                'roundId': str(random.randint(100000, 999999)),
                'multiplier': round(random.uniform(1.05, 5.5), 2),
                'timestamp': (datetime.utcnow() - timedelta(minutes=i)).isoformat(),
                'crashMultiplier': round(random.uniform(1.2, 6.0), 2),
                'result': random.choice(['crashed', 'completed', 'pending'])
            }
            for i in range(limit)
        ]


class GanymedConnector(PlatformConnector):
    """Connector for Ganymed_Hack Aviator variant."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key', '')
        self.api_url = config.get('api_url', 'https://ganymed.hack')
        self.authenticated = False

    def authenticate(self) -> bool:
        """Authenticate with Ganymed API."""
        try:
            if self.api_key:
                self.authenticated = True
                return True
            return False
        except Exception as e:
            print(f"Ganymed authentication failed: {e}")
            return False

    def fetch_rounds(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch rounds from Ganymed API."""
        if not self.authenticated:
            return self._mock_ganymed_data(limit)

        try:
            rounds = self._mock_ganymed_data(limit)
            return self.normalize_data(rounds)
        except Exception as e:
            print(f"Failed to fetch Ganymed rounds: {e}")
            return self._mock_ganymed_data(limit)

    def fetch_live_round(self) -> Optional[Dict[str, Any]]:
        """Fetch current live round from Ganymed."""
        rounds = self.fetch_rounds(limit=1)
        return rounds[0] if rounds else None

    def normalize_data(self, raw_data: List[Dict]) -> List[Dict]:
        """Convert Ganymed format to standard format."""
        normalized = []
        for item in raw_data:
            normalized.append({
                'id': item.get('id', str(random.randint(1000, 9999))),
                'multiplier': float(item.get('value', 2.0)),
                'timestamp': item.get('time', datetime.utcnow().isoformat()),
                'crash_point': float(item.get('crash', 0)),
                'status': item.get('state', 'crashed'),
                'platform': 'ganymed'
            })
        return normalized

    @staticmethod
    def _mock_ganymed_data(limit: int) -> List[Dict[str, Any]]:
        """Generate mock Ganymed-formatted data."""
        return [
            {
                'id': f"ganymed_{i}",
                'value': round(random.uniform(1.2, 4.8), 2),
                'time': (datetime.utcnow() - timedelta(minutes=i)).isoformat(),
                'crash': round(random.uniform(1.5, 5.5), 2),
                'state': random.choice(['crashed', 'completed'])
            }
            for i in range(limit)
        ]


class PlatformRegistry:
    """Registry for managing multiple platform connectors."""

    def __init__(self):
        self.connectors = {
            'spribe': SpribeConnector,
            'stake': StakeConnector,
            'ganymed': GanymedConnector,
        }
        self.active_connector = None

    def register_connector(self, name: str, connector_class: type) -> None:
        """Register a new platform connector."""
        if not issubclass(connector_class, PlatformConnector):
            raise ValueError(f"{connector_class} must inherit from PlatformConnector")
        self.connectors[name.lower()] = connector_class
        print(f"Registered connector: {name}")

    def get_connector(self, platform: str, config: Dict[str, Any]) -> Optional[PlatformConnector]:
        """Get a connector instance for the specified platform."""
        connector_class = self.connectors.get(platform.lower())
        if not connector_class:
            raise ValueError(f"Unknown platform: {platform}. Available: {list(self.connectors.keys())}")
        return connector_class(config)

    def list_platforms(self) -> List[str]:
        """List all registered platforms."""
        return list(self.connectors.keys())


# Global registry instance
registry = PlatformRegistry()
