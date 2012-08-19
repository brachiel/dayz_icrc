from django.contrib import admin
from django import forms
from models import Player, Case, CaseNote
from django.db.models import Q
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
    
    drop_case = forms.BooleanField(required=False, label="Drop this case. This will remove yourself from the case, even if you're the last medic. For this, make sure the above medic list is completely empty, first.")

class Assignment(admin.SimpleListFilter):
    title = "Assignment"
    
    parameter_name = "assignment"
    
    def lookups(self, request, model_admin):
        return (("own","Own"), ("unassigned","Unassigned"), ("editable", "Own or Unassigned"))

    def queryset(self, request, queryset):
        if self.value() == "own":
            return queryset.filter(medics=request.user.player)
        if self.value() == "unassigned":
            return queryset.filter(medics__isnull=True)
        if self.value() == "editable":
            return queryset.filter(Q(medics=request.user.player) | Q(medics__isnull=True))
        
        return queryset

class OnlyMedicsFilter(admin.SimpleListFilter):
    title = "Medic"
    
    parameter_name = "medic"
    
    def lookups(self, request, model_admin):
        return [(p.name, p.name) for p in Player.objects.filter(type=1)]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(medics__name=self.value())
        else:
            return queryset

class CaseAdmin(admin.ModelAdmin):
    def get_medic_list(self, x):
        return ', '.join([p.name for p in x.medics.all()])
    
    get_medic_list.short_description = "Medics"
    
    list_display = ('status', 'patient', 'get_medic_list', 'created', 'last_updated')
    list_filter = (Assignment, OnlyMedicsFilter, 'status', )
    
    readonly_fields = ['id_string', 'patient', 'status']
    
    fieldsets = (
        ("Case", {'fields': ('id_string', 'status', 'patient', 'medics', 'drop_case')}),
        ("Case Note", {'fields': ('new_status', 'note', )}),
    )
    
    form = CaseAdminForm
    
    def changelist_view(self, request, extra_context=None): # Set default filter to "Own or Unassigned"
        referer = request.META.get('HTTP_REFERER', '') 
        test = referer.split(request.META['PATH_INFO'])
        
        if test[-1] and not test[-1].startswith('?') and not request.GET.has_key('assignment'):
            q = request.GET.copy()
            q['assignment'] = 'editable'
            request.GET = q
            request.META['QUERY_STRING'] = request.GET.urlencode()
            
        return super(CaseAdmin,self).changelist_view(request, extra_context=extra_context)
    
    def save_model(self, request, obj, form, change):
        if form.is_valid():
            new_status = form.cleaned_data['new_status']
            note = form.cleaned_data['note']
            drop_case = form.cleaned_data['drop_case']
            
            if new_status == obj.status or new_status == "None":
                new_status = None

            if not note:
                note = ""

            if drop_case:
                obj.medics.remove(request.user.player)
                
                if obj.medics.count() == 0: # Dropped the last medic. We will post the note, and reopen the case.
                    if new_status is not None or len(note) > 0:
                        new_note = CaseNote(case=obj, author=request.user.player, note=note, new_status=new_status)
                        new_note.save()
                    
                    drop_note = "The case was dropped by the medic. It was reopened for assignment."
                    for x,y in form.cleaned_data.items():
                        drop_note += "%s: %s" % (x,y)
                    drop_note += str(form.cleaned_data)
                    new_note = CaseNote(case=obj, author=request.user.player, note=drop_note, new_status=0)
                    new_note.save()
                    
                    obj.status = 0
                    
                    obj.save()
                    return
            
            if not (new_status is not None or len(note) > 0):
                obj.save()
                return
            
            if new_status is not None:
                obj.status = new_status
            
            new_note = CaseNote(case=obj, author=request.user.player, note=note, new_status=new_status)
            new_note.save()
            
            obj.save()
        else:
            obj.save()
            
    # Permissions
    def has_change_permission(self, request, obj=None):
        if obj is None: 
            return True # Editing of this type of object is allowed in general
        
        if request.user.has_perm('medic_finder.edit_all_cases'):
            return True
        
        if obj.medics.count() == 0:
            return True
        
        medic = request.user.player
        
        if medic in obj.medics.all():
            return True
        
        return False
        
admin.site.register(Player) # not for normal medics
admin.site.register(Case, CaseAdmin)
admin.site.register(CaseNote) # not for normal medics

