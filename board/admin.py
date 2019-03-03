from django.contrib import admin
from .models import Sprint, Task


# Register your models here.

@admin.register(Sprint)
class SprintAdmin(admin.ModelAdmin):
    pass


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    pass
