import logging
from django.conf import settings
from .sapi_helpers import vech_imei, writelocation, writestatus, getstatus
from .sapi_broadcaster import publish_cast

logger = logging.getLogger(__name__)


def handle_write(auth, ptype, data, request=None):
    """Main router for device writes. Returns array of per-item results similar to PHP script.

    - auth: auth token from device
    - ptype: protocol type (e.g., 'gt06')
    - data: parsed JSON array of device messages
    """
    # simple auth check
    allowed = getattr(settings, 'SAPI_AUTH_KEYS', [])
    if auth not in allowed:
        raise Exception('unauthorized')

    results = []
    if ptype.lower() == 'gt06':
        for d in data:
            try:
                r = _handle_gt06_item(d)
            except Exception as e:
                logger.exception('gt06 item error')
                r = {'ok': False, 'error': str(e)}
            results.append(r)
    else:
        raise Exception(f'unsupported protocol: {ptype}')

    return results


def _handle_gt06_item(d):
    """Process a single GT06-style message dict.

    Expected fields (examples): imei, event ('location'|'status'), lat, lon, satCnt,
    fixTimestamp, speed, terminalInfo (for status)
    """
    imei = d.get('imei') or d.get('deviceid')
    if not imei:
        return {'ok': False, 'error': 'missing imei'}

    veh = vech_imei(imei)

    ev = d.get('event', '').lower()
    if ev == 'location' or 'lat' in d and 'lon' in d:
        mdata = {
            'lat': float(d.get('lat')) if d.get('lat') is not None else None,
            'lon': float(d.get('lon')) if d.get('lon') is not None else None,
            'satCnt': int(d.get('satCnt') or d.get('sat') or 0),
            'fixTimestamp': d.get('fixTimestamp') or d.get('parseTime'),
            'speed': float(d.get('speed') or 0),
            'bearing': d.get('bearing'),
            'odometer': d.get('odometer')
        }
        ok = writelocation(veh, mdata)
        cast = {
            'type': 'location',
            'imei': imei,
            'data': mdata,
            'vehicle': veh.veh_id if veh else None,
            'status': getstatus(veh) if veh else 'unknown'
        }
        # publish cast to configured broadcaster (redis/http)
        try:
            publish_cast(cast)
        except Exception:
            logger.exception('publish cast failed')
        return {'ok': ok, 'cast': cast}

    elif ev == 'status' or 'terminalInfo' in d or 'voltageLevel' in d:
        term = d.get('terminalInfo', {})
        mdata = {
            'battery': d.get('voltageLevel') or d.get('battery'),
            'ignition': term.get('ignition') if isinstance(term, dict) else d.get('ignition'),
            'gps': term.get('gpsTracking') if isinstance(term, dict) else d.get('gps'),
            'gsm': d.get('gsmSigStrength') or d.get('slevel'),
            'charging': term.get('charging') if isinstance(term, dict) else d.get('charging')
        }
        ok = writestatus(veh, mdata)
        cast = {
            'type': 'status',
            'imei': imei,
            'data': mdata,
            'vehicle': veh.veh_id if veh else None,
            'status': getstatus(veh) if veh else 'unknown'
        }
        try:
            publish_cast(cast)
        except Exception:
            logger.exception('publish cast failed')
        return {'ok': ok, 'cast': cast}

    else:
        return {'ok': False, 'error': 'unknown event'}
