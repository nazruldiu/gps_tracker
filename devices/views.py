from django.shortcuts import render
from .models import Device
from clients.models import Admin
from django.utils import timezone
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from . import sapi_handlers
from django.views.decorators.http import require_POST
from vehicles.models import Vehicle


@csrf_exempt
@require_POST
def assign_device(request):
    """Assign or update a device record to point to a vehicle.

    POST fields: imei, veh_id, number, sim, type, password
    """
    imei = request.POST.get('imei')
    veh_id = request.POST.get('veh_id')
    if not imei:
        return JsonResponse({'ok': False, 'error': 'missing imei'}, status=400)

    if not veh_id:
        return JsonResponse({'ok': False, 'error': 'missing veh_id'}, status=400)

    try:
        v = Vehicle.objects.get(veh_id=int(veh_id))
    except Vehicle.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'vehicle not found'}, status=404)

    # Update Vehicle.imei directly (the vehicles table already has IMEI)
    v.imei = imei
    v.save()

    # If a Device exists with this IMEI, link it to the vehicle but do not create or delete devices.
    from .models import Device
    try:
        dev = Device.objects.filter(imei=imei).first()
        if dev:
            dev.veh = v
            # update optional fields if provided
            for f in ('number', 'sim', 'type', 'password'):
                val = request.POST.get(f)
                if val is not None:
                    setattr(dev, f, val)
            dev.save()
    except Exception:
        # do not fail the whole request if device update fails
        pass

    return JsonResponse({'ok': True, 'veh_id': v.veh_id, 'imei': v.imei})

# Create your views here.
def add_device(request):
    if request.method == 'POST':
        imei = request.POST.get('imei')
        number = request.POST.get('number')
        sim = request.POST.get('sim')
        type = request.POST.get('type')

        device = Device(
            user_id=1,
            client=Admin.objects.get(admin_id=1),
            # veh_id= null ,
            imei=imei,
            mdms='',
            number=number,
            sim=sim,
            type=type,
            password='',
            date = timezone.now().date(),
            time = timezone.now().time(),
        ).save()
        # You can add more fields as necessary

    return render(request, 'devices/add_device.html')

def all_devices(request):
    devices = Device.objects.all()
    return render(request, 'devices/all_devices.html', {'devices': devices})


@csrf_exempt
def sapi_v1_write(request):
    """Endpoint compatible with PHP `sapi_v1_write.php` used by GT06 gateways.

    Expects POST fields: auth, type, data (JSON array)
    """
    if request.method != 'POST':
        return HttpResponse(status=405)

    auth = request.POST.get('auth') or request.POST.get('AUTH')
    ptype = request.POST.get('type') or request.POST.get('TYPE')
    data_raw = request.POST.get('data') or request.POST.get('DATA')

    if not (auth and ptype and data_raw):
        return HttpResponseBadRequest('missing auth/type/data')

    try:
        data = json.loads(data_raw)
    except Exception:
        return HttpResponseBadRequest('invalid json in data')

    # delegate to handlers
    try:
        result = sapi_handlers.handle_write(auth, ptype, data, request)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)

    return JsonResponse({'ok': True, 'result': result})