import os
import sys
from pathlib import Path

# Ensure project root (frontend2) is on sys.path so `settings` can be imported
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
import django
django.setup()
from core.models import Usuario

# Define users to ensure: (username, email, rol, password, is_superuser)
users = [
    ('admin', 'admin@local', 'administrador', 'admin123', True),
    ('gerente', 'gerente@local', 'gerente', 'gerente123', False),
    ('vendedor', 'vendedor@local', 'vendedor', 'vendedor123', False),
    ('cocina', 'cocina@local', 'cocina', 'cocina123', False),
]

for username, email, rol, pwd, is_super in users:
    obj, created = Usuario.objects.get_or_create(username=username, defaults={'email': email, 'rol': rol, 'is_superuser': is_super, 'is_staff': is_super})
    if not created:
        obj.email = email
        obj.rol = rol
        obj.is_superuser = is_super
        obj.is_staff = is_super
    obj.set_password(pwd)
    obj.save()
    print(f"{username}|{email}|{rol}|{pwd}|is_super={is_super}")
