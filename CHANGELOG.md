# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2025-01-03

Rework to [hyper-modern structure](https://cjolowicz.github.io/posts/hypermodern-python-01-setup/)

### Improvements
- Use [python-pdm](https://pdm-project.org/)
- Use src layout
- Use ruff linter and formatter
- Implement tests (100% coverage)
- Publish to [PyPI](https://pypi.org/) index

## [0.9.0] - 2024-12-16

Setter and several new queries.

### Features
- New Queries:
  - live_wallbox
  - live_powermeter
  - static_system
- Setter:
  - power_limits
  - powersave
  - weather_regulated_charge

## [0.1.0] - 2024-11-26

Initial version.

### Features
- Query live status (system, batteries, inverter, ...)
- Query historical data (day, month, ...)
- Multiple queries
- Machine-readable JSON output
