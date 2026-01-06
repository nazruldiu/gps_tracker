from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from clients.models import Admin

class Vehicle(models.Model):
    class DisabledStatus(models.TextChoices):
        YES = 'y', 'Yes'
        NO = 'n', 'No'

    class Status(models.TextChoices):
        YES = 'y', 'Yes'
        NO = 'n', 'No'

    class ConnectionStatus(models.TextChoices):
        CONNECTED = 'y', 'Connected'
        DISCONNECTED = 'n', 'Disconnected'

    class RelayStatus(models.TextChoices):
        ON = 'on', 'On'
        OFF = 'off', 'Off'

    class PublicPrivacy(models.TextChoices):
        ALL = 'all', 'All'
        PRIVATE = 'private', 'Private'
        # Add more as needed

    veh_id = models.AutoField(primary_key=True)
    user_id = models.IntegerField()
    client_id = models.ForeignKey(Admin, on_delete=models.CASCADE, null=True, blank=True)
    imei = models.CharField(max_length=255, unique=True)  # IMEI should be unique
    name = models.CharField(max_length=255, default='')
    reg_no = models.CharField(max_length=255, unique=True)  # Registration number should be unique
    odometer = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    type = models.CharField(max_length=255)
    milage = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    low_fuel = models.BooleanField(default=False)
    overspeed = models.BooleanField(default=False)
    ignition = models.BooleanField(default=False)
    connection = models.CharField(
        max_length=1,
        choices=ConnectionStatus.choices,
        default=ConnectionStatus.DISCONNECTED
    )
    connection_time = models.DateTimeField(null=True, blank=True)
    locked = models.BooleanField(default=False)
    online = models.BooleanField(default=False)
    gps = models.BooleanField(default=False)
    sat = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(20)])
    charging = models.BooleanField(default=False)
    battery = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    telecom = models.CharField(max_length=255, null=True, blank=True)
    blevel = models.IntegerField(
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    slevel = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    speed = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    current_fuel = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    longi = models.DecimalField(max_digits=12, decimal_places=8, null=True, blank=True)
    lat = models.DecimalField(max_digits=12, decimal_places=8, null=True, blank=True)
    vstatus = models.CharField(max_length=255, default='', blank=True)
    stime = models.DateTimeField(null=True, blank=True)
    bearing = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    tkm = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tkm_date = models.DateField(null=True, blank=True)
    udis = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    relay = models.BooleanField(default=False)
    relaystate = models.CharField(
        max_length=5,
        choices=RelayStatus.choices,
        default=RelayStatus.ON
    )
    last_place = models.TextField(blank=True)
    geocode = models.BooleanField(default=False)
    geocode_txt = models.TextField(blank=True)
    geocode_time = models.DateTimeField(null=True, blank=True)
    alt = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    check_alt = models.BooleanField(default=False)
    alt_time = models.DateTimeField(null=True, blank=True)
    alt_txt = models.CharField(max_length=255, blank=True)
    last_date = models.DateField(null=True, blank=True)
    last_time = models.TimeField(null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    public = models.BooleanField(default=False)
    public_privacy = models.CharField(
        max_length=25,
        choices=PublicPrivacy.choices,
        default=PublicPrivacy.ALL
    )
    date = models.DateField(auto_now_add=True)  # Auto set on creation
    time = models.TimeField(auto_now_add=True)  # Auto set on creation
    disabled = models.CharField(
        max_length=1,
        choices=DisabledStatus.choices,
        default=DisabledStatus.NO
    )
    status = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.YES
    )

    def __str__(self):
        return f"{self.name} ({self.reg_no})"


class VehicleLocation(models.Model):
    id = models.AutoField(primary_key=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='locations')
    lat = models.DecimalField(max_digits=12, decimal_places=8)
    lon = models.DecimalField(max_digits=12, decimal_places=8)
    speed = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    sat = models.IntegerField(null=True, blank=True)
    time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-time', '-created_at']

    def __str__(self):
        return f"Loc {self.vehicle_id} @ {self.lat},{self.lon} ({self.time})"