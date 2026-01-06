"""CLI to create or update Device records and link them to Vehicles.

Usage examples:
  python scripts/update_device_info.py --imei 868720063708337 --veh 1 --number 0123 --sim 99999 --type gt06
  python scripts/update_device_info.py --csv devices.csv

CSV expected columns: imei,veh_id,number,sim,type,password
"""
import argparse
import csv
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neo_track.settings')
import django
django.setup()

from devices.models import Device
from vehicles.models import Vehicle
from clients.models import Admin
from django.utils import timezone


def update_device(imei, veh_id=None, number='', sim='', type='gt06', password=''):
    defaults = {
        'user_id': 1,
        'mdms': '',
        'number': number or '',
        'sim': sim or '',
        'type': type or 'gt06',
        'password': password or '',
        'date': timezone.now().date(),
        'time': timezone.now().time(),
        'disabled': 'n',
        'status': 'y',
    }

    dev, created = Device.objects.get_or_create(imei=str(imei), defaults={**defaults, 'client': Admin.objects.first() if Admin.objects.exists() else None})
    if not created:
        for k, v in defaults.items():
            setattr(dev, k, v)

    if veh_id:
        try:
            veh = Vehicle.objects.get(veh_id=int(veh_id))
            dev.veh = veh
        except Vehicle.DoesNotExist:
            print(f'Warning: vehicle id {veh_id} not found')

    dev.save()
    print(f"Device {'created' if created else 'updated'}: id={dev.device_id} imei={dev.imei} veh={dev.veh_id}")


def process_csv(path):
    with open(path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            update_device(row.get('imei'), row.get('veh_id'), row.get('number'), row.get('sim'), row.get('type'), row.get('password'))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--imei')
    p.add_argument('--veh', dest='veh_id')
    p.add_argument('--number')
    p.add_argument('--sim')
    p.add_argument('--type')
    p.add_argument('--password')
    p.add_argument('--csv')
    args = p.parse_args()

    if args.csv:
        process_csv(args.csv)
        return

    if not args.imei:
        print('Provide --imei or --csv')
        return

    update_device(args.imei, args.veh_id, args.number, args.sim, args.type, args.password)


if __name__ == '__main__':
    main()
