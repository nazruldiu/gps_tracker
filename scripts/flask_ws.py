"""Simple Flask + SocketIO server to query device GPS by IMEI.

Usage:
  pip install flask flask-socketio eventlet
  python scripts/flask_ws.py

The server listens for SocketIO event `get_gps` with payload `{'imei': '...'}`
and emits `gps_info` with the query result.
"""
import os
import logging

from flask import Flask
from flask_socketio import SocketIO, emit

# configure Django settings so we can import project models/helpers
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neo_track.settings')
import django
django.setup()

from devices.sapi_helpers import get_gps_info_by_imei

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-me'
socketio = SocketIO(app, cors_allowed_origins='*')


@app.route('/')
def index():
    return 'Flask SocketIO GPS bridge'


@socketio.on('get_gps')
def handle_get_gps(payload):
    imei = None
    try:
        if isinstance(payload, dict):
            imei = payload.get('imei')
        else:
            imei = payload
    except Exception:
        imei = None

    if not imei:
        emit('gps_info', {'ok': False, 'error': 'missing imei'})
        return

    try:
        info = get_gps_info_by_imei(imei)
        if not info:
            emit('gps_info', {'ok': False, 'error': 'not found', 'imei': imei})
        else:
            emit('gps_info', {'ok': True, 'data': info})
    except Exception as e:
        logger.exception('error processing get_gps')
        emit('gps_info', {'ok': False, 'error': str(e)})


@socketio.on('cast')
def handle_incoming_cast(cast):
    """Accept `cast` objects from upstream publishers and broadcast to clients.

    This allows Django (or other services) to emit casts by connecting as a
    Socket.IO client and emitting `cast` events — the server will re-broadcast
    to all connected browser clients.
    """
    try:
        # re-broadcast to all connected clients
        socketio.emit('cast', cast, broadcast=True)
    except Exception:
        logger.exception('failed to broadcast cast')


if __name__ == '__main__':
    # eventlet recommended for Flask-SocketIO; ensure it's installed
    try:
        import eventlet
        eventlet.monkey_patch()
    except Exception:
        pass
    socketio.run(app, host='0.0.0.0', port=6791)
