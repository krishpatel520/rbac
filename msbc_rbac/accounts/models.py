from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.conf import settings

from msbc_rbac.core.models import Role, ApiOperation
from decouple import config

# Configure RBAC_TENANT_MODEL - defaults to 'core.Tenant' if not set

settings.TENANT_MODEL = config("TENANT_MODEL", default="core.tenant")

PROJECT_SCOPE = config("PROJECT_SCOPE", default="accounts")


class UserManager(BaseUserManager):
    """
    Custom user manager that enforces tenant assignment.
    """

    def create_user(self, username, email=None, password=None, tenant=None, **extra_fields):
        is_superuser = extra_fields.get("is_superuser", False)
        if not username:
            raise ValueError("The Username must be set")
        if tenant is None and not is_superuser:
            raise ValueError("User must belong to a tenant")

        email = self.normalize_email(email)
        user = self.model(
            username=username,
            email=email,
            tenant=tenant,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, tenant=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(
            username=username,
            email=email,
            password=password,
            tenant=tenant,
            **extra_fields,
        )


class User(AbstractUser):
    """
    Custom user model for the RBAC system.

    Each user belongs to exactly one tenant (Organization).
    This extends the default Django AbstractUser.
    """
    tenant = models.ForeignKey(
        settings.TENANT_MODEL,
        blank=False,
        null=True,
        on_delete=models.PROTECT,
        related_name="users",
    )

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='rbac_users',
        blank=True
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='rbac_users',
        blank=True
    )

    objects = UserManager()

    def __str__(self):
        return f"{self.username} ({self.tenant})"


class UserRole(models.Model):
    """
    Represents the assignment of a Role to a User.

    This is a many-to-many relationship model between User and Role.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_roles",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="role_users",
    )

    tenant = models.ForeignKey(
        settings.TENANT_MODEL,
        blank=False,
        null=True,
        on_delete=models.PROTECT,
        related_name=f"{PROJECT_SCOPE}_users",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "role"],
                name="unique_user_role",
            )
        ]

    def __str__(self):
        return f"{self.user} → {self.role}"


class UserApiBlock(models.Model):
    """
    Represents a specific API operation blocked for a specific user within a tenant.

    This allows for granular restriction of capabilities even if the user's role 
    nominally permits the action.
    """
    tenant = models.ForeignKey(
        settings.TENANT_MODEL,
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    api_operation = models.ForeignKey(ApiOperation, on_delete=models.CASCADE)
    reason = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ('tenant', 'user', 'api_operation')
