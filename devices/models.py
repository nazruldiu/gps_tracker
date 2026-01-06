from django.db import models
from clients.models import Admin
from vehicles.models import Vehicle
class Device(models.Model):
    class DisabledStatus(models.TextChoices):
        YES = 'y', 'Yes'
        NO = 'n', 'No'

    class Status(models.TextChoices):
        YES = 'y', 'Yes'
        NO = 'n', 'No'

    device_id = models.AutoField(primary_key=True)
    user_id = models.IntegerField()
    client = models.ForeignKey(Admin, on_delete=models.CASCADE, null=True, blank=True)
    veh = models.ForeignKey(Vehicle, on_delete=models.CASCADE, null=True, blank=True)
    imei = models.CharField(max_length=255)
    mdms = models.CharField(max_length=20, default='')
    number = models.CharField(max_length=255)
    sim = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField()
    disabled = models.CharField(
        max_length=1,
        choices=DisabledStatus.choices
    )
    status = models.CharField(
        max_length=1,
        choices=Status.choices
    )
    def __str__(self):
        return f"Device {self.device_id} - {self.imei}"

