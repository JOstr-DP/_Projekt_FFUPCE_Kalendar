from django import forms

from .models import Event


class EventCreateForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title',
            'description',
            'date',
            'location',
            'difficulty',
            'teacher',
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
