from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from .managers import UserManager
from django.utils import timezone
class User(AbstractBaseUser, PermissionsMixin):
    # Remove UUID primary key
    # user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ROLE_CHOICES = (
        ('SUPERUSER', 'Superuser'),
        ('MANAGER', 'Manager'),
        ('USER', 'User'),
    )
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    rating = models.IntegerField(default=1200,null=True,blank=True)
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

    # Override groups and permissions to avoid clash
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='USER',
        db_index=True
    )


    @property
    def is_staff(self):
        return self.is_admin or self.role == 'MANAGER'
    @property
    def is_manager(self):
        return self.role == 'MANAGER'

    @property
    def is_regular_user(self):
        return self.role == 'USER'


    def save(self, *args, **kwargs):
        # Keep role and is_superuser in sync
        if self.is_superuser:
            self.role = 'SUPERUSER'
            self.is_admin = True
        super().save(*args, **kwargs)


class UserStatistics(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='statistics'
    )
    total_solved = models.IntegerField(default=0)
    acceptance_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    current_streak = models.IntegerField(default=0)

