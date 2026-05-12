from django import forms

from .models import Event, Teacher


class EventCreateForm(forms.ModelForm):
	"""
	Formulář pro vytváření a editaci akce.
	
	Pole:
	- title, description, date, location, teacher_name, capacity, reference, guest
	
	# Pole se váže na datalist v šabloně event_create.html pro návrh jmen
	Speciální logika:
	- teacher_name: textové pole s našeptáváním (datalist)
		- Hledá existujícího učitele case-insensitive
		- Nikdy nevytváří nového učitele
		- Validuje: teacher musí existovat v DB
	"""
    teacher_name = forms.CharField(
        label='Teacher',
        max_length=120,
        help_text='Zacnete psat jmeno a vyberte existujiciho ucitele, nebo zadejte nove jmeno.',
        widget=forms.TextInput(attrs={'list': 'teacher-list', 'placeholder': 'napr. Jana Novakova'}),
    )

    class Meta:
        model = Event
        fields = [
            'title',
            'description',
            'date',
            'location',
            'teacher_name',
            'capacity',
            'reference',
            'guest',
        ]
        widgets = {
            'date': forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Načtení seznamu všech učitelů pro datalist (našeptávání)
        self.teacher_name_choices = list(
            Teacher.objects.order_by('name').values_list('name', flat=True)
        )
        # Při editaci: naplnit pole jménem stávajícího učitele   Teacher.objects.order_by('name').values_list('name', flat=True)
        )
        if self.instance and self
        """
        Validace: Učitel musí existovat v DB.
        Case-insensitive hledání.
        Ukládá si _matched_teacher pro použití v save().
        """.instance.pk and self.instance.teacher_id:
            self.fields['teacher_name'].initial = self.instance.teacher.name

    def clean_teacher_name(self):
        teacher_name = self.cleaned_data['teacher_name'].strip()
        if not teacher_name:
        """
        Validace: Kapacita musí být > 0.
        """
            raise forms.ValidationError('Ucitel je povinny.')
        teacher = Teacher.objects.filter(name__iexact=teacher_name).first()
        if teacher is None:
            raise forms.Validati
        """
        Uložení: Přiřadí vybraného učitele (ze self._matched_teacher).
        """onError('Ucitel nebyl nalezen v databazi. Vyberte prosim existujici jmeno.')
        self._matched_teacher = teacher
        return teacher_name

    def clean_capacity(self):
        capacity = self.cleaned_data['capacity']
        if capacity <= 0:
            raise forms.ValidationError('Kapacita musi byt vyssi nez 0.')
        return capacity

    def save(self, commit=True):
        event = super().save(commit=False)
        event.teacher = self._matched_teacher
        if commit:
            event.save()
        return event
