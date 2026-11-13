
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile


admin.site.register(User, UserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'city', 'state', 'created_at')
    search_fields = ('user__username', 'phone_number', 'city')
    list_filter = ('state', 'city')

