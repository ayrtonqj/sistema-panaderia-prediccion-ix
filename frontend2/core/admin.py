from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'email', 'rol', 'is_active', 'is_staff')
    list_filter = ('rol', 'is_active', 'is_staff')
    search_fields = ('username', 'email')
    ordering = ('username',)

    fieldsets = UserAdmin.fieldsets + (
        ('Rol', {'fields': ('rol', 'telefono')}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Rol', {'fields': ('rol', 'email', 'telefono')}),
    )
