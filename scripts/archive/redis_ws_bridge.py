#!/usr/bin/env python3
"""
Archive: redis_ws_bridge.py

This file was the original Redis->WebSocket bridge. It has been
deprecated in favor of `scripts/flask_ws.py` (Socket.IO bridge). The
contents are preserved here for historical/reference purposes.
"""

# Deprecated: use scripts/flask_ws.py
from __future__ import annotations

import logging

logging.getLogger(__name__).warning('redis_ws_bridge (archived) - use flask_ws.py')
