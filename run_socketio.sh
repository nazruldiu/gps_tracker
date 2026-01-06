#!/bin/bash
cd /home/neo_track
. venv/bin/activate
exec python scripts/flask_ws.py --host 0.0.0.0 --port 6791