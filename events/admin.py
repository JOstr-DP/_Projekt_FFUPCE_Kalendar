from django.contrib import admin

from .models import Event, EventTemplate, Registration, Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
	list_display = ('id', 'name', 'department')
	search_fields = ('name', 'department')


@admin.register(EventTemplate)
class EventTemplateAdmin(admin.ModelAdmin):
	list_display = ('id', 'title', 'location', 'capacity', 'is_archived')
	list_filter = ('is_archived', 'filling_strategy')
	search_fields = ('title', 'location')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
	list_display = ('id', 'title', 'date', 'location', 'capacity', 'teacher')
	list_filter = ('teacher', 'filling_strategy')
	search_fields = ('title', 'location')


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
	list_display = ('id', 'event', 'status', 'timestamp')
	list_filter = ('status',)
	search_fields = ('user_id_hashed', 'event__title')
