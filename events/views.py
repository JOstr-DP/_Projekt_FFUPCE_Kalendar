from datetime import timedelta

from django.contrib import messages
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import EventCreateForm
from .models import Event, Registration, Teacher


# Interni role + mapovani pro uzivatelsky text v UI.
ALLOWED_ROLES = {'admin', 'teacher', 'ambassador', 'viewer', 'student'}

ROLE_LABELS = {
	'admin': 'Admin',
	'teacher': 'Teacher',
	'ambassador': 'Ambasador',
	'viewer': 'Viewer',
}


def _bootstrap_demo_events() -> None:
	"""Vytvori demo ucitele a akce pouze pokud databaze nema zadne akce."""
	with transaction.atomic():
		if Event.objects.exists():
			return

		demo_teachers = [
			('Jana Novakova', 'Katedra historie'),
			('Petr Svoboda', 'Katedra informatiky'),
			('Lucie Prochazkova', 'Katedra bohemistiky'),
		]

		teacher_map = {}
		for name, department in demo_teachers:
			teacher, _ = Teacher.objects.get_or_create(name=name, defaults={'department': department})
			teacher_map[name] = teacher

		now = timezone.now().replace(minute=0, second=0, microsecond=0)
		demo_events = [
			{
				'title': 'Digitalni archiv v praxi',
				'description': 'Zaklady prace s univerzitnim digitalnim archivem.',
				'date': now + timedelta(days=2, hours=10),
				'location': 'Aula FF UPCE',
				'capacity': 25,
				'teacher': teacher_map['Jana Novakova'],
			},
			{
				'title': 'Den otevrenych dveri FF',
				'description': 'Ambasadori pomahaji s organizaci a orientaci navstevniku.',
				'date': now + timedelta(days=4, hours=8),
				'location': 'Hlavni vestibul',
				'capacity': 40,
				'teacher': teacher_map['Petr Svoboda'],
			},
			{
				'title': 'Workshop oral history',
				'description': 'Priprava techniky a asistence behem rozhovoru.',
				'date': now + timedelta(days=6, hours=9),
				'location': 'Ucebna B203',
				'capacity': 18,
				'teacher': teacher_map['Lucie Prochazkova'],
			},
			{
				'title': 'Studentska konference DH',
				'description': 'Pomoc s registraci a koordinaci programu.',
				'date': now + timedelta(days=9, hours=7),
				'location': 'Konferencni sal 1',
				'capacity': 30,
				'teacher': teacher_map['Jana Novakova'],
			},
			{
				'title': 'Komentovana prohlidka expozice',
				'description': 'Ambasadori zajistuji podporu navstevnikum.',
				'date': now + timedelta(days=12, hours=11),
				'location': 'Univerzitni galerie',
				'capacity': 20,
				'teacher': teacher_map['Petr Svoboda'],
			},
		]

		for payload in demo_events:
			Event.objects.create(
				filling_strategy='FIFO',
				created_by_role='admin',
				created_by_identity='System',
				**payload,
			)


def _can_manage_event(role: str, actor_identity: str, event: Event) -> bool:
	"""Admin muze vse, teacher pouze vlastni akce."""
	if role == 'admin':
		return True
	if role == 'teacher':
		return event.created_by_role == 'teacher' and event.created_by_identity == actor_identity
	return False


def role_login(request):
	"""Prihlaseni role a inicializace demo dat pri prazdne DB."""
	_bootstrap_demo_events()
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
	"""Prehled metrik a nejblizsich akci."""
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
	"""Seznam akci s filtry podle nazvu, ucitele a mista."""
	role = request.session.get('selected_role')
	if not role:
		return redirect('role_login')

	queryset = Event.objects.select_related('teacher').all()
	q = request.GET.get('q', '').strip()
	teacher = request.GET.get('teacher', '').strip()
	location = request.GET.get('location', '').strip()

	if q:
		queryset = queryset.filter(title__icontains=q)
	if teacher:
		queryset = queryset.filter(teacher__name__icontains=teacher)
	if location:
		queryset = queryset.filter(location__icontains=location)

	events = queryset.order_by('date')
	context = {
		'role': role,
		'events': events,
		'filters': {
			'q': q,
			'teacher': teacher,
			'location': location,
		},
	}
	return render(request, 'events/event_list.html', context)


def event_detail(request, event_id: int):
	"""Detail akce + prava pro edit/smazani."""
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
	"""Vytvoreni akce. Povoleny pouze role admin/teacher."""
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
	"""Editace akce. Povoleny admin a vlastnik akce."""
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
	"""Smazani akce. Pouze POST a opravneny uzivatel."""
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
	"""Odhlaseni uzivatele a navrat na login."""
	request.session.pop('selected_role', None)
	request.session.pop('actor_identity', None)
	messages.info(request, 'Byl(a) jste odhlasen(a).')
	return redirect('role_login')
