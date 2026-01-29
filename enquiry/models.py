from django.db import models
from core.models import Tenant
from core.managers import TenantAwareManager


class EnquiryStatus(models.TextChoices):
    NEW = "NEW", "New"
    QUALIFIED = "QUALIFIED", "Qualified"
    DISQUALIFIED = "DISQUALIFIED", "Disqualified"
    CLOSED = "CLOSED", "Closed"


class Enquiry(models.Model):
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="enquiries",
    )

    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField(blank=True)
    subject = models.CharField(max_length=255)

    status = models.CharField(
        max_length=20,
        choices=EnquiryStatus.choices,
        default=EnquiryStatus.NEW,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantAwareManager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "status"]),
        ]

    def __str__(self):
        return f"{self.subject} ({self.status})"
