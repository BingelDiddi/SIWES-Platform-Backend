from django.contrib import admin
from .models import LogEntry, FinalReport

admin.site.register(LogEntry)
admin.site.register(FinalReport)