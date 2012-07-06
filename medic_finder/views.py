from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, permission_required
from django import forms

from medic_finder.models import Player, Case, CaseNote
import random

def get_punchline():
	punchlines = ["Because a life expectancy of 30 minutes is just not enough.",
			  "Fixing broken bones with morphine since Day Z.",
			  "Because medical supplies are not just lying around in random houses.",
			  "Call us, and we'll help you... maybe... if we don't get shot... or shoot you first..."]
	return random.choice(punchlines)

class NewCaseForm(forms.Form):
	player_name = forms.CharField(max_length=50, required=True, label="In-game survivor name.")
	case_description = forms.CharField(max_length=4000, min_length=30, required=True, label="Case description.")
	case_description.widget = forms.Textarea()
	case_description.initial = """Describe your problem.
* DO NOT FORGET to include where you are.
* DO NOT FORGET to include when you are online / when you need help."""

	latitude = forms.IntegerField(required=True, min_value=-13669, max_value=0)
	longitude = forms.IntegerField(required=True, min_value=0, max_value=16660)


def new_case_form(request):
	error_message = "BlahBlah"
	
	if request.method == 'POST': # If the form has been submitted...
		form = NewCaseForm(request.POST)
		
		if form.is_valid(): # Let's rock'n'roll
			player_name = form.cleaned_data['player_name']
			case_description = form.cleaned_data['case_description']
			
			latitude = form.cleaned_data['latitude']
			longitude = form.cleaned_data['longitude']
			
			player, created = Player.objects.get_or_create(name=player_name)
			
			case = Case(patient=player, latitude=latitude, longitude=longitude)
			case.save()
			
			case_note = CaseNote(case=case, author=player, note=case_description)
			case_note.save()
			
			return HttpResponseRedirect('cases/show/' + case.id_string + '/')
		else:
			error_message = "There was an error filling out the form"
			for x,y in request.POST.items():
				error_message += "\n%s: %s" % (x,y)
			#return HttpResponse(error_message)

	form = NewCaseForm()
	
	t = loader.get_template('cases/new.html')
	c = RequestContext(request, { 'form': form, 'error_message': error_message, 'punchline': get_punchline() })
	return HttpResponse(t.render(c))

def logout(request):
	if request.user.is_authenticated:
		auth_logout(request)

	return HttpResponseRedirect('./')
