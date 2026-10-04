# Example Plugin: Custom Aviator Platform

This directory shows how to create a custom platform connector plugin.

## Structure

```
example_platform/
├── __init__.py
├── connector.py      # Main connector implementation
└── config.json      # Configuration template
```

## To Use This Example

1. Copy this directory to `plugins/your_platform/`
2. Edit `connector.py` with your platform's API details
3. Set `PLATFORM_NAME` to your platform identifier
4. Backend will auto-load on startup

## Required Connector Methods

- `authenticate()` - Verify API connection
- `fetch_rounds(limit)` - Fetch historical rounds
- `fetch_live_round()` - Get current round
- `normalize_data(raw_data)` - Convert to standard format

## Standard Data Format

All connectors must normalize to:

```python
{
    'id': str,              # Unique round ID
    'multiplier': float,    # Final multiplier
    'timestamp': str,       # ISO format timestamp
    'crash_point': float,   # Where round crashed
    'status': str,          # 'crashed' | 'pending' | 'completed'
    'platform': str         # Platform name
}
```

## See Also

- `../../INTEGRATION_GUIDE.md` - Full integration guide
- `../../backend/connectors.py` - Base connector class
- `../../backend/multi_platform.py` - Data service
