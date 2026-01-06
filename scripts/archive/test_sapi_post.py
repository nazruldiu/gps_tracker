#!/usr/bin/env python3
"""
Archive: test_sapi_post.py

Preserved test script used to POST sample SAPI payloads to the Django endpoint.
"""
import requests
import json

URL = 'http://localhost:8000/devices/sapi_v1_write/'

payload = {
    'auth': 'SAUTH',
    'type': 'gt06',
    'data': json.dumps([
        {
            'imei': '123456789012345',
            'event': 'location',
            'lat': 24.8607,
            'lon': 67.0011,
            'satCnt': 7,
            'fixTimestamp': 1700000000000,
            'speed': 45.3
        },
        {
            'imei': '123456789012345',
            'event': 'status',
            'terminalInfo': {'ignition': True, 'gpsTracking': True, 'charging': False},
            'voltageLevel': 12.6,
            'gsmSigStrength': 4
        }
    ])
}

if __name__ == '__main__':
    r = requests.post(URL, data=payload)
    print(r.status_code)
    print(r.text)
