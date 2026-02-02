from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserApiBlock


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


@admin.register(UserApiBlock)
class UserApiBlockAdmin(admin.ModelAdmin):
    list_display = ("tenant","user","api_operation", "reason")