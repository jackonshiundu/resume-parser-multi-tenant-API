from django.contrib import admin

from .models import (
    Candidate,
    Resume,
)

# Register your models here.
admin.site.register(Resume)
admin.site.register(Candidate)
