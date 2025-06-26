"""
Plugin System
=============

Sistema de plugins extensível para PythonKore.
"""

from base_plugin import BasePlugin, PluginInfo, PluginStatus, PluginType
from plugin_manager import PluginManager
# from plugin_loader import PluginLoader
# from hook_system import HookSystem

__all__ = ['PluginManager', 'BasePlugin', 'PluginInfo', 'PluginStatus', 'PluginType'] 