"""Plugin system for Aviator Predictor Pro.

Allows third-party developers to create custom platform connectors.
"""

import os
import sys
import importlib.util
from pathlib import Path
from typing import Type, Dict, Any
from connectors import PlatformConnector, registry


class PluginManager:
    """Manages loading and registration of custom connector plugins."""

    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(exist_ok=True)
        self.loaded_plugins = {}

    def load_plugin(self, plugin_name: str) -> bool:
        """Load a plugin from the plugins directory.
        
        Expected plugin structure:
        plugins/
          my_platform/
            __init__.py
            connector.py  (contains MyPlatformConnector class)
            config.json
        """
        plugin_path = self.plugins_dir / plugin_name
        
        if not plugin_path.exists():
            print(f"Plugin directory not found: {plugin_path}")
            return False

        try:
            connector_path = plugin_path / "connector.py"
            if not connector_path.exists():
                print(f"Connector module not found: {connector_path}")
                return False

            # Load the connector module dynamically
            spec = importlib.util.spec_from_file_location(
                f"plugins.{plugin_name}.connector",
                connector_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find the connector class (must inherit from PlatformConnector)
            connector_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, PlatformConnector) and 
                    attr is not PlatformConnector):
                    connector_class = attr
                    break

            if not connector_class:
                print(f"No PlatformConnector subclass found in {connector_path}")
                return False

            # Register the connector
            platform_name = getattr(module, 'PLATFORM_NAME', plugin_name)
            registry.register_connector(platform_name, connector_class)
            self.loaded_plugins[plugin_name] = {
                'class': connector_class,
                'path': plugin_path,
                'platform_name': platform_name
            }

            print(f"✓ Plugin loaded: {plugin_name} -> {platform_name}")
            return True

        except Exception as e:
            print(f"✗ Failed to load plugin {plugin_name}: {e}")
            return False

    def load_all_plugins(self) -> int:
        """Load all plugins from the plugins directory."""
        if not self.plugins_dir.exists():
            print(f"Plugins directory not found: {self.plugins_dir}")
            return 0

        loaded_count = 0
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir() and not plugin_dir.name.startswith('_'):
                if self.load_plugin(plugin_dir.name):
                    loaded_count += 1

        return loaded_count

    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin."""
        if plugin_name in self.loaded_plugins:
            del self.loaded_plugins[plugin_name]
            print(f"Plugin unloaded: {plugin_name}")
            return True
        return False

    def list_loaded_plugins(self) -> Dict[str, Any]:
        """Return information about loaded plugins."""
        return self.loaded_plugins
