from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Show tenant when EDITING a user
    fieldsets = UserAdmin.fieldsets + (
        ("Tenant Information", {"fields": ("tenant",)}),
    )

    # Show tenant when ADDING a user 
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Tenant Information",
            {
                "fields": ("tenant",),
            },
        ),
    )

    list_display = UserAdmin.list_display + ("tenant",)
    list_filter = UserAdmin.list_filter + ("tenant",)
