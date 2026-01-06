from django.conf import settings
from .models import Device
from vehicles.models import Vehicle
from django.utils import timezone
from vehicles.models import VehicleLocation
import logging
import json

logger = logging.getLogger(__name__)

try:
    from elasticsearch import Elasticsearch
    ES_AVAILABLE = True
except Exception:
    ES_AVAILABLE = False


def vech_imei(imei):
    """Return Vehicle instance for an IMEI (or None)."""
    try:
        dev = Device.objects.filter(imei=imei).select_related('veh').first()
        if dev and dev.veh:
            return dev.veh
        # fallback: try vehicle with same imei
        return Vehicle.objects.filter(imei=imei).first()
    except Exception:
        logger.exception('vech_imei error')
        return None


def getstatus(vehicle: Vehicle):
    """Compute a compact status string for the vehicle.

    This mirrors the PHP `getstatus()` used by the front-end to pick icons.
    We'll return one of: 'moving', 'stopped', 'idle', 'unknown'
    """
    try:
        if not vehicle:
            return 'unknown'
        speed = float(vehicle.speed or 0)
        if speed > 5:
            return 'moving'
        elif vehicle.ignition:
            return 'idle'
        else:
            return 'stopped'
    except Exception:
        logger.exception('getstatus error')
        return 'unknown'


def _es_client():
    dsn = getattr(settings, 'ELASTICSEARCH_DSN', '')
    if not dsn or not ES_AVAILABLE:
        return None
    return Elasticsearch([dsn])


def writelocation(veh: Vehicle, mdata: dict):
    """Update Vehicle object and optionally write to Elasticsearch index `veh_locations`.

    mdata expected keys: lat, lon, speed, satCnt, fixTimestamp, bearing, odometer
    """
    try:
        if not veh:
            logger.warning('writelocation called without vehicle')
            return False

        veh.lat = mdata.get('lat')
        veh.longi = mdata.get('lon')
        veh.speed = mdata.get('speed') or 0
        veh.sat = mdata.get('satCnt') or 0
        veh.bearing = mdata.get('bearing')
        ts = mdata.get('fixTimestamp')
        if ts:
            try:
                # assume ISO or unix ms
                if isinstance(ts, (int, float)):
                    veh.stime = timezone.datetime.fromtimestamp(float(ts) / 1000, tz=timezone.utc)
                else:
                    veh.stime = timezone.datetime.fromisoformat(ts)
            except Exception:
                pass

        od = mdata.get('odometer')
        if od is not None:
            try:
                veh.odometer = od
            except Exception:
                pass

        veh.last_time = timezone.now().date()
        veh.save()

        # persist history to DB as fallback (and for track history)
        try:
            if veh:
                # store as VehicleLocation
                VehicleLocation.objects.create(
                    vehicle=veh,
                    lat=veh.lat,
                    lon=veh.longi,
                    speed=veh.speed or 0,
                    sat=veh.sat or 0,
                    time=veh.stime
                )
        except Exception:
            logger.exception('store VehicleLocation failed')

        # write to ES
        es = _es_client()
        if es:
            doc = {
                'veh_id': veh.veh_id,
                'imei': veh.imei,
                'lat': float(veh.lat) if veh.lat is not None else None,
                'lon': float(veh.longi) if veh.longi is not None else None,
                'speed': float(veh.speed or 0),
                'time': veh.stime.isoformat() if veh.stime else timezone.now().isoformat(),
            }
            try:
                es.index(index='veh_locations', body=doc)
            except Exception:
                logger.exception('es index veh_locations failed')

        return True
    except Exception:
        logger.exception('writelocation error')
        return False


def writestatus(veh: Vehicle, mdata: dict):
    """Update status-related vehicle fields and optionally write to ES `veh_status`.

    mdata expected keys: battery, ignition, gps, gsm, charging
    """
    try:
        if not veh:
            logger.warning('writestatus called without vehicle')
            return False

        b = mdata.get('battery')
        if b is not None:
            try:
                veh.battery = float(b)
            except Exception:
                pass

        ign = mdata.get('ignition')
        if ign is not None:
            veh.ignition = bool(ign)

        gps = mdata.get('gps')
        if gps is not None:
            veh.gps = bool(gps)

        veh.slevel = mdata.get('gsm') or veh.slevel
        veh.charging = bool(mdata.get('charging', veh.charging))
        veh.last_time = timezone.now().date()
        veh.save()

        es = _es_client()
        if es:
            doc = {
                'veh_id': veh.veh_id,
                'imei': veh.imei,
                'battery': veh.battery,
                'ignition': veh.ignition,
                'gps': veh.gps,
                'time': timezone.now().isoformat(),
            }
            try:
                es.index(index='veh_status', body=doc)
            except Exception:
                logger.exception('es index veh_status failed')

        return True
    except Exception:
        logger.exception('writestatus error')
        return False


def get_gps_info_by_imei(imei: str):
    """Return a dict with GPS/status info for a given IMEI or None if not found.

    Uses existing `Device` and `Vehicle` relations and `getstatus()` for a compact status.
    """
    try:
        if not imei:
            return None

        # try to find device and related vehicle
        dev = Device.objects.filter(imei=imei).select_related('veh').first()
        veh = None
        if dev and getattr(dev, 'veh', None):
            veh = dev.veh
        else:
            # fallback: vehicle with same imei
            veh = Vehicle.objects.filter(imei=imei).first()

        if not dev and not veh:
            return None

        info = {'imei': imei}
        if dev:
            info.update({
                'device_id': getattr(dev, 'id', None),
                'device_obj': None,  # placeholder, avoid serializing model instances
            })

        if veh:
            info.update({
                'veh_id': getattr(veh, 'veh_id', None),
                'name': getattr(veh, 'name', None),
                'lat': getattr(veh, 'lat', None),
                'lon': getattr(veh, 'longi', None),
                'speed': float(getattr(veh, 'speed', 0) or 0),
                'stime': getattr(veh, 'stime', None).isoformat() if getattr(veh, 'stime', None) else None,
                'status': getstatus(veh),
            })

        return info
    except Exception:
        logger.exception('get_gps_info_by_imei error')
        return None
