"""Publish `cast` objects to a Flask-SocketIO bridge.

This project has been consolidated to use a Socket.IO bridge. The Django
handler calls `publish_cast()` which will connect to the configured
`SAPI_SOCKETIO_URL` (default: http://127.0.0.1:6791) and emit a `cast` event.

Requires `python-socketio` to be installed in the Django environment.
"""
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def _publish_socketio(msg: str) -> bool:
    try:
        import socketio
        url = getattr(settings, 'SAPI_SOCKETIO_URL', '') or 'http://127.0.0.1:6791'
        sio = socketio.Client()
        # short-lived connect/emit/disconnect pattern keeps implementation simple
        sio.connect(url, wait=True, transports=['websocket'])
        sio.emit('cast', json.loads(msg))
        sio.disconnect()
        return True
    except Exception:
        logger.exception('socketio publish failed')
        return False


def publish_cast(cast: dict) -> bool:
    """Publish the `cast` dict to the Socket.IO bridge.

    Returns True if the publish succeeded.
    """
    try:
        msg = json.dumps(cast, default=str)
    except Exception:
        logger.exception('failed to json encode cast')
        return False

    ok = _publish_socketio(msg)
    if not ok:
        logger.debug('cast not published via Socket.IO')
    return ok
