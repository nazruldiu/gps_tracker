import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neo_track.settings')
import django
django.setup()

from devices import sapi_handlers

data = [
    {'imei': '123456789012345', 'event': 'location', 'lat': 24.8607, 'lon': 67.0011, 'satCnt': 7, 'fixTimestamp': 1700000000000, 'speed': 45.3},
    {'imei': '123456789012345', 'event': 'status', 'terminalInfo': {'ignition': True, 'gpsTracking': True, 'charging': False}, 'voltageLevel': 12.6, 'gsmSigStrength': 4}
]

try:
    res = sapi_handlers.handle_write('SAUTH', 'gt06', data, None)
    print('result:', res)
except Exception as e:
    import traceback
    traceback.print_exc()
