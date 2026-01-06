import os
import sys
from pathlib import Path
from django.utils import timezone

# ensure project root is on path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neo_track.settings')
import django
django.setup()

from vehicles.models import Vehicle, VehicleLocation
from devices.models import Device
from clients.models import Admin
import datetime

def create_vehicle_and_device(imei, name='Device', reg_no=None):
    reg_no = reg_no or imei[-6:]
    veh, created = Vehicle.objects.get_or_create(imei=str(imei), defaults={
        'user_id': 1,
        'client_id': Admin.objects.first() if Admin.objects.exists() else None,
        'name': name,
        'reg_no': reg_no,
        'type': 'gt06',
        'date': timezone.now().date(),
        'time': timezone.now().time(),
    })
    if created:
        print('Created Vehicle', veh.veh_id)
    else:
        print('Vehicle exists', veh.veh_id)

    dev, dcreated = Device.objects.get_or_create(imei=str(imei), defaults={
        'user_id': 1,
        'client': Admin.objects.first() if Admin.objects.exists() else None,
        'veh': veh,
        'mdms': '',
        'number': '',
        'sim': '',
        'type': 'gt06',
        'password': '',
        'date': timezone.now().date(),
        'time': timezone.now().time(),
        'disabled': 'n',
        'status': 'y',
    })
    if not dcreated and dev.veh is None:
        dev.veh = veh
        dev.save()

    print('Device', dev.device_id, 'linked to Vehicle', veh.veh_id)
    return veh, dev


def add_location(veh, lat, lon, speed=0, when=None):
    when = when or timezone.now()
    loc = VehicleLocation.objects.create(
        vehicle=veh,
        lat=lat,
        lon=lon,
        speed=speed,
        sat=0,
        time=when
    )
    print('Inserted VehicleLocation id', loc.id)
    return loc


if __name__ == '__main__':
    # replace these with your values
    imei = '868720063708337'
    lat = 27.713262
    lon = 85.291256
    speed = 0
    # Date:2006-04-08 Time:13:19:36
    when = datetime.datetime(2006, 4, 8, 13, 19, 36)
    # make timezone-aware in UTC
    when = timezone.make_aware(when, timezone.utc)

    v, d = create_vehicle_and_device(imei, name='Imported Device', reg_no='IMP'+imei[-4:])
    add_location(v, lat, lon, speed, when)

    print('Done. Open /vehicles/track or /vehicles/track/{} to view.'.format(v.veh_id))
