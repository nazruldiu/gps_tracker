from django.db import models

# Create your models here.

class Admin(models.Model):
    class Status(models.TextChoices):
        YES = 'y', 'Active'
        NO = 'n', 'Inactive'

    class DisabledStatus(models.TextChoices):
        YES = 'y', 'Disabled'
        NO = 'n', 'Enabled'

    class DeletedStatus(models.TextChoices):
        YES = 'y', 'Deleted'
        NO = 'n', 'Active'

    admin_id = models.AutoField(primary_key=True)
    fullname = models.TextField()
    username = models.TextField(unique=True)
    image = models.IntegerField(default=0)
    email = models.TextField()
    password = models.TextField()
    role = models.CharField(
        max_length=10, blank=True
    )
    renew_type = models.CharField(max_length=255, default='', blank=True)
    renew_cost = models.CharField(max_length=255, default='', blank=True)
    recharge_type = models.CharField(max_length=255, default='', blank=True)
    services = models.CharField(max_length=500, default='', blank=True)
    disabled = models.CharField(
        max_length=1,
        choices=DisabledStatus.choices
    )
    deleted = models.CharField(
        max_length=20,
        choices=DeletedStatus.choices,
        default=DeletedStatus.NO
    )
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(
        max_length=1,
        choices=Status.choices
    )

    def __str__(self):
        return f"{self.fullname} ({self.role})"