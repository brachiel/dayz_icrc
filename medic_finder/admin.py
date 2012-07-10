from django.contrib import admin
from django import forms
from models import Player, Case, CaseNote
#import logging

#logger = logging.getLogger('console')

class CaseAdminForm(forms.ModelForm):
    class Meta:
        model = Case
    
    def __init__(self, *args, **kwargs):
        super(CaseAdminForm, self).__init__(*args, **kwargs)
        
        self.fields["medics"].queryset = Player.objects.filter(type=1)
    
    new_status = forms.ChoiceField(required=False, choices=( ((None,""),) + Case.STATUS_CHOICES[1:] ))
    
    note = forms.CharField(max_length=4000, required=False, label="New Case Note")
    note.widget = forms.Textarea()

class OnlyMedicsFilter(admin.SimpleListFilter):
    title = "Medic"
    
    parameter_name = "medic"
    
    def lookups(self, request, model_admin):
        return [(p.name, p.name) for p in Player.objects.filter(type=1)]
    
    def queryset(self, request, queryset):
        if (self.value()):
            return queryset.filter(medics__name=self.value())
        else:
            return queryset

class CaseAdmin(admin.ModelAdmin):
    def get_medic_list(self, x):
        return ', '.join([p.name for p in x.medics.all()])
    get_medic_list.short_description = "Medics"
    
    list_display = ('status', 'patient', 'get_medic_list', 'created', 'last_updated')
    list_filter = (OnlyMedicsFilter, 'status', )
    
    readonly_fields = ['id_string', 'status']
    
    fieldsets = (
        ("Case", {'fields': ('id_string', 'status', 'patient', 'medics')}),
        ("Case Note", {'fields': ('new_status', 'note', )}),
    )
    
    form = CaseAdminForm
    
    def save_model(self, request, obj, form, change):
        if form.is_valid():
            new_status = form.cleaned_data['new_status']
            note = form.cleaned_data['note']
            
            if (new_status == obj.status or new_status == "None"):
                new_status = None

            if (not note):
                note = ""

            if not (new_status is not None or len(note) > 0):
                obj.save()
                return
            
            obj.status = new_status
            
            new_note = CaseNote(case=obj, author=request.user.player, note=note, new_status=new_status)
            new_note.save()
            
            obj.save()
        else:
            obj.save()

admin.site.register(Player)
admin.site.register(Case, CaseAdmin)
admin.site.register(CaseNote)

