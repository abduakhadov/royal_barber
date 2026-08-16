import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings'); django.setup(); from barber.models import Zone; print(list(Zone.objects.all().values()))
