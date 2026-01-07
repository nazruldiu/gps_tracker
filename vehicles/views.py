from django.shortcuts import render
from .models import Vehicle
from clients.models import Admin
from django.utils import timezone
from django.views.decorators.http import require_GET
import json

# Create your views here.
# Create your views here.
def add_vehicle(request):
    if request.method == 'POST':
        imei = request.POST.get('imei')
        reg_no = request.POST.get('reg_no')
        name = request.POST.get('name')
        odometer = request.POST.get('odometer', 0)
        milage = request.POST.get('milage', 0)
        low_fuel = request.POST.get('low_fuel')
        overspeed = request.POST.get('overspeed')
        type = request.POST.get('type')
        public_privacy = request.POST.get('public_privacy')
        public = True if public_privacy == 'YES' else False

        vehicle = Vehicle(
            imei=imei,
            user_id=1,
            client_id=Admin.objects.get(admin_id=1),
            reg_no=reg_no,
            name=name,
            odometer=odometer,
            milage=milage,
            low_fuel=low_fuel == 'on',
            overspeed=overspeed == 'on',
            type=type,
            public=public,
            date = timezone.now().date(),
            time = timezone.now().time(),
        ).save()

    return render(request, 'vehicles/add_vehicle.html')

def all_vehicles(request):
    vehicles = Vehicle.objects.all()
    return render(request, 'vehicles/all_vehicles.html', {'vehicles': vehicles})

def vehicles_report(request):
    vehicles = Vehicle.objects.all()
    return render(request, 'vehicles/vehicles_report.html', {'vehicles': vehicles})

def vehicles_status(request):
    vehicles = Vehicle.objects.all()
    return render(request, 'vehicles/vehicles_status.html', {'vehicles': vehicles})

@require_GET
def track_view(request, veh_id: int = None):
    """Vehicle tracking page.
    If `veh_id` is provided, load recent `VehicleLocation` history and pass as JSON
    for the template to render a polyline.
    """
    vehicles = Vehicle.objects.all()
    history = []
    if veh_id:
        try:
            v = Vehicle.objects.get(veh_id=veh_id)
            locs = v.locations.all().order_by('time')[:1000]
            # build simple list of [lat,lon,time]
            for l in locs:
                history.append({'imei': l.vehicle.imei, 'speed': float(l.speed), 'lat': float(l.lat), 'lon': float(l.lon), 'time': l.time.isoformat() if l.time else None})
        except Vehicle.DoesNotExist:
            history = []

    return render(request, 'vehicles/vehicles_track.html', {'vehicles': vehicles, 'history_json': json.dumps(history), 'selected_veh_id': veh_id})

@require_GET
def current_view(request, veh_id: int = None):
    """Vehicle current location page (latest point only)."""
    vehicles = Vehicle.objects.all()
    history = []

    if veh_id:
        try:
            v = Vehicle.objects.get(veh_id=veh_id)

            # ✅ GET ONLY LATEST LOCATION
            loc = v.locations.order_by('-time').first()

            if loc:
                history = [{
                    'imei': v.imei,
                    'speed': float(loc.speed),
                    'lat': float(loc.lat),
                    'lon': float(loc.lon),
                    'time': loc.time.isoformat() if loc.time else None
                }]

        except Vehicle.DoesNotExist:
            history = []

    return render(
        request,
        'vehicles/vehicles_current_location.html',
        {
            'vehicles': vehicles,
            'history_json': json.dumps(history),
            'selected_veh_id': veh_id
        }
    )