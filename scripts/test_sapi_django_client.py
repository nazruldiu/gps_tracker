import os
import sys
from pathlib import Path
import django
from django.test import Client

# ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neo_track.settings')
django.setup()

client = Client()

payload = {
    'auth': 'SAUTH',
    'type': 'gt06',
    'data': '[{"imei":"123456789012345","event":"location","lat":24.8607,"lon":67.0011,"satCnt":7,"fixTimestamp":1700000000000,"speed":45.3},{"imei":"123456789012345","event":"status","terminalInfo":{"ignition":true,"gpsTracking":true,"charging":false},"voltageLevel":12.6,"gsmSigStrength":4}]'
}

resp = client.post('/devices/sapi_v1_write/', data=payload)
print('status_code:', resp.status_code)
content = resp.content.decode('utf-8')
print('content (truncated 1000 chars):')
print(content[:1000])
if resp.status_code >= 500:
    # dump full content to a file for inspection
    with open('scripts/sapi_error_response.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Full 500 HTML written to scripts/sapi_error_response.html')
