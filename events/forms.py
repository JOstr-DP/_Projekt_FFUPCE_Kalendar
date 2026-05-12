from django import forms

from .models import Event, Teacher


class EventCreateForm(forms.ModelForm):
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
            'difficulty',
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
        self.fields['date'].input_formats = ['%Y-%m-%dT%H:%M']
        self.teacher_name_choices = list(
            Teacher.objects.order_by('name').values_list('name', flat=True)
        )
        if self.instance and self.instance.pk and self.instance.teacher_id:
            self.fields['teacher_name'].initial = self.instance.teacher.name

    def clean_teacher_name(self):
        teacher_name = self.cleaned_data['teacher_name'].strip()
        if not teacher_name:
            raise forms.ValidationError('Ucitel je povinny.')
        teacher = Teacher.objects.filter(name__iexact=teacher_name).first()
        if teacher is None:
            raise forms.ValidationError('Ucitel nebyl nalezen v databazi. Vyberte prosim existujici jmeno.')
        self._matched_teacher = teacher
        return teacher_name

    def clean_difficulty(self):
        difficulty = self.cleaned_data['difficulty']
        if difficulty < 1 or difficulty > 5:
            raise forms.ValidationError('Narocnost musi byt v intervalu 1-5.')
        return difficulty

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
