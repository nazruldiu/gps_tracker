This project adds a simple SAPI-compatible endpoint for GT06 device messages.

Endpoints:
- POST /devices/sapi_v1_write/  - fields: auth, type, data (JSON array)

Setup:
- Add `SAPI_AUTH_KEYS = ['SAUTH']` and `ELASTICSEARCH_DSN` in settings.py (already configured with defaults).
- Install requirements: `pip install -r requirements.txt`
- Run Django server: `python manage.py runserver`

Test:
- Run `python scripts/test_sapi_post.py` (requires `requests` and server running locally)

Notes:
- Elasticsearch writes are optional and require `ELASTICSEARCH_DSN` in settings.
- The handler expects device `imei` mapping to `Device` -> `veh` relation or `Vehicle.imei`.
