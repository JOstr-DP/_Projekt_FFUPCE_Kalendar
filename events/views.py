from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EventCreateForm
from .models import Event, Registration


ALLOWED_ROLES = {'admin', 'teacher', 'ambassador', 'viewer', 'student'}

ROLE_LABELS = {
	'admin': 'Admin',
	'teacher': 'Teacher',
	'ambassador': 'Ambasador',
	'viewer': 'Viewer',
}


def _can_manage_event(role: str, actor_identity: str, event: Event) -> bool:
	if role == 'admin':
		return True
	if role == 'teacher':
		return event.created_by_role == 'teacher' and event.created_by_identity == actor_identity
	return False


def role_login(request):
	if request.method == 'POST':
		role = request.POST.get('role', '').strip().lower()
		if role == 'student':
			role = 'ambassador'
		identity = request.POST.get('identity', '').strip()
		if role in ALLOWED_ROLES:
			request.session['selected_role'] = role
			role_label = ROLE_LABELS.get(role, role.title())
			request.session['actor_identity'] = identity or role_label
			messages.success(request, f'Prihlaseno jako: {role_label}')
			return redirect('dashboard')
		messages.error(request, 'Neplatna role.')

	return render(request, 'events/login.html')


def dashboard(request):
	role = request.session.get('selected_role')
	if not role:
		return redirect('role_login')

	events_total = Event.objects.count()
	upcoming_events = Event.objects.order_by('date')[:5]
	registrations_total = Registration.objects.exclude(status=Registration.STATUS_CANCELLED).count()
	waitlist_total = Registration.objects.filter(status=Registration.STATUS_WAITLIST).count()
	status_counts = Registration.objects.values('status').annotate(total=Count('id')).order_by()

	context = {
		'role': role,
		'role_label': ROLE_LABELS.get(role, role.title()),
		'events_total': events_total,
		'registrations_total': registrations_total,
		'waitlist_total': waitlist_total,
		'upcoming_events': upcoming_events,
		'status_counts': status_counts,
	}
	return render(request, 'events/dashboard.html', context)


def event_list(request):
	role = request.session.get('selected_role')
	if not role:
		return redirect('role_login')

	queryset = Event.objects.select_related('teacher').all()
	q = request.GET.get('q', '').strip()
	teacher = request.GET.get('teacher', '').strip()
	location = request.GET.get('location', '').strip()
	difficulty = request.GET.get('difficulty', '').strip()

	if q:
		queryset = queryset.filter(title__icontains=q)
	if teacher:
		queryset = queryset.filter(teacher__name__icontains=teacher)
	if location:
		queryset = queryset.filter(location__icontains=location)
	if difficulty.isdigit():
		queryset = queryset.filter(difficulty=int(difficulty))

	events = queryset.order_by('date')
	context = {
		'role': role,
		'events': events,
		'filters': {
			'q': q,
			'teacher': teacher,
			'location': location,
			'difficulty': difficulty,
		},
	}
	return render(request, 'events/event_list.html', context)


def event_detail(request, event_id: int):
	role = request.session.get('selected_role')
	actor_identity = request.session.get('actor_identity', '')
	if not role:
		return redirect('role_login')

	event = get_object_or_404(Event.objects.select_related('teacher'), pk=event_id)
	context = {
		'role': role,
		'event': event,
		'can_delete_event': _can_manage_event(role, actor_identity, event),
		'can_edit_event': _can_manage_event(role, actor_identity, event),
	}
	return render(request, 'events/event_detail.html', context)


def event_create(request):
	role = request.session.get('selected_role')
	actor_identity = request.session.get('actor_identity', '')
	if not role:
		return redirect('role_login')

	if role not in {'admin', 'teacher'}:
		messages.error(request, 'Pro vytvareni udalosti nemate opravneni.')
		return redirect('event_list')

	if request.method == 'POST':
		form = EventCreateForm(request.POST)
		if form.is_valid():
			event = form.save(commit=False)
			event.filling_strategy = 'FIFO'
			event.created_by_role = role
			event.created_by_identity = actor_identity or role.title()
			event.save()
			messages.success(request, 'Udalost byla uspesne vytvorena.')
			return redirect('event_detail', event_id=event.id)
	else:
		form = EventCreateForm()

	return render(request, 'events/event_create.html', {'role': role, 'form': form})


def event_edit(request, event_id: int):
	role = request.session.get('selected_role')
	actor_identity = request.session.get('actor_identity', '')
	if not role:
		return redirect('role_login')

	event = get_object_or_404(Event, pk=event_id)
	if not _can_manage_event(role, actor_identity, event):
		messages.error(request, 'Pro upravu teto udalosti nemate opravneni.')
		return redirect('event_detail', event_id=event_id)

	if request.method == 'POST':
		form = EventCreateForm(request.POST, instance=event)
		if form.is_valid():
			updated_event = form.save(commit=False)
			updated_event.filling_strategy = 'FIFO'
			updated_event.save()
			messages.success(request, 'Udalost byla uspesne upravena.')
			return redirect('event_detail', event_id=updated_event.id)
	else:
		form = EventCreateForm(instance=event)

	context = {
		'role': role,
		'form': form,
		'event': event,
		'edit_mode': True,
	}
	return render(request, 'events/event_create.html', context)


def event_delete(request, event_id: int):
	role = request.session.get('selected_role')
	actor_identity = request.session.get('actor_identity', '')
	if not role:
		return redirect('role_login')
	if request.method != 'POST':
		return redirect('event_detail', event_id=event_id)

	event = get_object_or_404(Event, pk=event_id)
	if not _can_manage_event(role, actor_identity, event):
		messages.error(request, 'Pro smazani teto udalosti nemate opravneni.')
		return redirect('event_detail', event_id=event_id)

	title = event.title
	event.delete()
	messages.success(request, f'Udalost "{title}" byla smazana.')
	return redirect('event_list')


def logout_view(request):
	request.session.pop('selected_role', None)
	request.session.pop('actor_identity', None)
	messages.info(request, 'Byl(a) jste odhlasen(a).')
	return redirect('role_login')
