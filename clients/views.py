from django.shortcuts import render
from .models import Admin
from django.utils import timezone
# Create your views here.
def add_client(request):
    if request.method == 'POST':
        fullname = request.POST.get('client_name')
        renew_cost = request.POST.get('renew_cost')
        renew_type = request.POST.get('renew_type')
        recharge_type = request.POST.get('recharge_type')

        username = request.POST.get('mobile')
        email = request.POST.get('email')
        # password = request.POST.get('password')
        # role = request.POST.get('role')

        client = Admin(
            fullname=fullname,
            renew_cost=renew_cost,
            renew_type=renew_type,
            recharge_type=recharge_type,

            username=username,
            email=email,
            # password=password,
            # role=role,
            date=timezone.now().date(),
            time=timezone.now().time(),
        ).save()
        # You can add more fields as necessary
    return render(request, 'clients/add_client.html')

def all_clients(request):
    clients = Admin.objects.all()
    return render(request, 'clients/all_clients.html', {'clients': clients})