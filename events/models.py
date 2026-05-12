from django.core.exceptions import ValidationError
from django.db import models


class Teacher(models.Model):
	name = models.CharField(max_length=120)
	department = models.CharField(max_length=120)

	def __str__(self) -> str:
		return self.name


class EventTemplate(models.Model):
	title = models.CharField(max_length=200)
	location = models.CharField(max_length=150)
	capacity = models.PositiveIntegerField()
	filling_strategy = models.CharField(max_length=20, default='FIFO')
	teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
	is_archived = models.BooleanField(default=False)
	created_by_role = models.CharField(max_length=20, default='teacher')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def clean(self) -> None:
		if not 1 <= self.difficulty <= 5:
			raise ValidationError({'difficulty': 'Difficulty must be in range 1-5.'})
		if self.capacity <= 0:
			raise ValidationError({'capacity': 'Capacity must be greater than zero.'})

	def __str__(self) -> str:
		return self.title


class Event(models.Model):
	title = models.CharField(max_length=200)
	description = models.TextField(blank=True, default='')
	date = models.DateTimeField()
	location = models.CharField(max_length=150)
	capacity = models.PositiveIntegerField()
	teacher = models.ForeignKey(Teacher, on_delete=models.PROTECT, related_name='events')
	reference = models.CharField(max_length=255, blank=True, default='')
	guest = models.CharField(max_length=120, blank=True, default='')
	created_by_role = models.CharField(max_length=20, blank=True, default='')
	created_by_identity = models.CharField(max_length=120, blank=True, default='')
	filling_strategy = models.CharField(max_length=20, default='FIFO')
	template = models.ForeignKey(EventTemplate, on_delete=models.SET_NULL, null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['date']

	def clean(self) -> None:
		if self.capacity <= 0:
			raise ValidationError({'capacity': 'Capacity must be greater than zero.'})

	def __str__(self) -> str:
		return f'{self.title} ({self.date:%d.%m.%Y %H:%M})'


class Registration(models.Model):
	STATUS_REGISTERED = 'registered'
	STATUS_WAITLIST = 'waitlist'
	STATUS_CANCELLED = 'cancelled'

	STATUS_CHOICES = [
		(STATUS_REGISTERED, 'Registered'),
		(STATUS_WAITLIST, 'Waitlist'),
		(STATUS_CANCELLED, 'Cancelled'),
	]

	event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
	user_id_hashed = models.CharField(max_length=64)
	timestamp = models.DateTimeField(auto_now_add=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_REGISTERED)

	class Meta:
		ordering = ['timestamp']

	def __str__(self) -> str:
		return f'{self.user_id_hashed[:10]}... - {self.event.title}'
