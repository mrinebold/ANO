"""
Plugins Module

Extension point for ANO framework profiles beyond the minimal base.

Plugins can register custom agents, policy presets, configuration overrides,
and integration hooks to adapt ANO for specific domains or use cases.

Structure:
- Each plugin is a Python package with a register(registry) function
- Plugins are loaded by the profile loader when selected
- Plugins build on top of the minimal profile base layer
"""
