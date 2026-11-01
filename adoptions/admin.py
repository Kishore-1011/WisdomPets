from django.contrib import admin

from .models import AdoptionRequest, Pet


class AdoptionRequestInline(admin.TabularInline):
    model = AdoptionRequest
    extra = 0
    fields = ['full_name', 'email', 'phone', 'status', 'created_at']
    readonly_fields = ['created_at']


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ['name', 'species', 'breed', 'age', 'sex']
    list_filter = ['species', 'sex']
    search_fields = ['name', 'breed']
    inlines = [AdoptionRequestInline]


@admin.register(AdoptionRequest)
class AdoptionRequestAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'pet', 'email', 'phone', 'status', 'created_at']
    list_filter = ['status', 'pet__species', 'created_at']
    list_editable = ['status']
    search_fields = ['full_name', 'email', 'pet__name']
    readonly_fields = ['created_at']
