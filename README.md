# TradeWatch

TradeWatch is a Python backend foundation for monitoring a configured market watchlist and supporting operational alerts. This repository currently contains only the Phase 1 project infrastructure.

## Current Phase

Phase 1 establishes configuration management, centralized logging, dependency declarations, and development tooling. It does not include trading logic, market data fetching, indicators, strategies, or database models.

## Setup

Requires Python 3.12 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## Running Locally

Load configuration from `config.yaml` and initialize logging from application code:

```python
from config import load_config
from logging_setup import setup_logging

settings = load_config("config.yaml")
logger = setup_logging(settings.logging)
logger.info("application_started")
```

## Project Structure

```text
.
├── config.py              # Typed YAML configuration loader
├── config.yaml            # Default local configuration
├── logging_setup.py       # Centralized console and rotating-file logging
├── pyproject.toml         # Python and tool configuration
├── requirements.txt       # Runtime dependencies
└── requirements-dev.txt   # Development dependencies
```
