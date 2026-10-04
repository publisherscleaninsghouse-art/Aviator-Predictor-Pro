"""Multi-platform data service for Aviator Predictor.

Handles data fetching, caching, and normalization across multiple platforms.
"""

import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from connectors import PlatformConnector, registry


class MultiPlatformDataService:
    """Service for managing data from multiple Aviator platforms."""

    def __init__(self, db_path: str = "data/aviator.db"):
        self.db_path = db_path
        self.active_platform = None
        self.connector = None
        self._init_platform_table()

    def _init_platform_table(self) -> None:
        """Initialize platform data table in database."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS platform_rounds (
                id TEXT PRIMARY KEY,
                platform TEXT NOT NULL,
                multiplier REAL NOT NULL,
                crash_point REAL,
                timestamp TEXT,
                status TEXT,
                cached_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        conn.close()

    def switch_platform(self, platform: str, config: Dict[str, Any]) -> bool:
        """Switch to a different platform and authenticate."""
        try:
            connector = registry.get_connector(platform, config)
            if connector.authenticate():
                self.connector = connector
                self.active_platform = platform
                print(f"Switched to platform: {platform}")
                return True
            return False
        except Exception as e:
            print(f"Failed to switch platform: {e}")
            return False

    def fetch_and_cache_rounds(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch rounds from active platform and cache them."""
        if not self.connector:
            raise ValueError("No active platform selected")

        rounds = self.connector.fetch_rounds(limit)
        self._cache_rounds(rounds)
        return rounds

    def fetch_live_round(self) -> Optional[Dict[str, Any]]:
        """Fetch the current live round from active platform."""
        if not self.connector:
            raise ValueError("No active platform selected")
        return self.connector.fetch_live_round()

    def _cache_rounds(self, rounds: List[Dict[str, Any]]) -> None:
        """Cache rounds in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for round_data in rounds:
            try:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO platform_rounds 
                    (id, platform, multiplier, crash_point, timestamp, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        round_data.get('id'),
                        round_data.get('platform', self.active_platform),
                        round_data.get('multiplier'),
                        round_data.get('crash_point'),
                        round_data.get('timestamp'),
                        round_data.get('status')
                    )
                )
            except Exception as e:
                print(f"Failed to cache round: {e}")

        conn.commit()
        conn.close()

    def get_cached_rounds(self, platform: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Retrieve cached rounds from database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if platform:
            cursor.execute(
                """
                SELECT * FROM platform_rounds 
                WHERE platform = ? 
                ORDER BY cached_at DESC 
                LIMIT ?
                """,
                (platform, limit)
            )
        else:
            cursor.execute(
                """
                SELECT * FROM platform_rounds 
                ORDER BY cached_at DESC 
                LIMIT ?
                """,
                (limit,)
            )

        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_platform_stats(self, platform: str, hours: int = 24) -> Dict[str, Any]:
        """Get statistics for a specific platform."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        cursor.execute(
            """
            SELECT 
                COUNT(*) as total_rounds,
                AVG(multiplier) as avg_multiplier,
                MAX(multiplier) as max_multiplier,
                MIN(multiplier) as min_multiplier,
                STDDEV(multiplier) as volatility
            FROM platform_rounds
            WHERE platform = ? AND cached_at > ?
            """,
            (platform, cutoff_time.isoformat())
        )

        stats = cursor.fetchone()
        conn.close()

        return {
            'platform': platform,
            'total_rounds': stats[0] or 0,
            'avg_multiplier': round(stats[1], 2) if stats[1] else 0,
            'max_multiplier': round(stats[2], 2) if stats[2] else 0,
            'min_multiplier': round(stats[3], 2) if stats[3] else 0,
            'volatility': round(stats[4], 2) if stats[4] else 0,
            'time_window_hours': hours
        }

    def list_available_platforms(self) -> List[str]:
        """List all available platforms."""
        return registry.list_platforms()
