from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, permission_required
from django import forms

from medic_finder.models import Player, Case, CaseNote, WeekTimeSpan
import random

import pytz

# Logging
import logging
logger = logging.getLogger("console")

## Other helper functions
def get_punchline():
	punchlines = ["Because a life expectancy of 50 minutes is just not enough.",
			  "Fixing broken bones with morphine since Day Z.",
			  "Because medical supplies do not just lie around in random houses.",
			  "Call us, and we'll help you... maybe... if we don't get shot... or get eaten by zombies...",
			  "The only friendlies in Cherno.",
			  "Please don't shoot us."]
	return random.choice(punchlines)


######### Views

class NewCaseForm(forms.Form):
	player_name = forms.CharField(max_length=50, required=True, label="In-game survivor name.")
	case_description = forms.CharField(max_length=4000, min_length=30, required=True, label="Case description.")
	case_description.widget = forms.Textarea()
	case_description.initial = """Describe your problem.
* DO NOT FORGET to include where you are.
* DO NOT FORGET to include when you are online / when you need help."""

	latitude = forms.IntegerField(required=True, min_value=-13669, max_value=0)
	longitude = forms.IntegerField(required=True, min_value=0, max_value=16660)
	
	timezone = forms.ChoiceField(choices=Case.TIMEZONE_CHOICES, label="Your timezone.")
	timetable = forms.CharField(max_length=1024, required=True)


def new_case_form(request):
	error_message = ""
	
	if request.method == 'POST': # If the form has been submitted...
		form = NewCaseForm(request.POST)
		
		if form.is_valid(): # Let's rock'n'roll
			player_name = form.cleaned_data['player_name']
			case_description = form.cleaned_data['case_description']
			
			latitude = form.cleaned_data['latitude']
			longitude = form.cleaned_data['longitude']
			
			timezone_id = int(form.cleaned_data['timezone'])
			timetable = form.cleaned_data['timetable'] # comma separated list of WeekTimeSpan ID's
			
			
			try:
				timezone = pytz.timezone(dict(Case.TIMEZONE_CHOICES)[timezone_id])
				
				weektimespans = []
				for name in timetable.split(','):
					weektimespans.append(WeekTimeSpan.objects.get_or_create_by_name(name, timezone))
					logger.debug(weektimespans)
				
				player, created = Player.objects.get_or_create(name=player_name)
				
				logger.debug(weektimespans)
				case = Case(patient=player, latitude=latitude, longitude=longitude, timezone=timezone_id)
				case.save()
				case.meeting_times = weektimespans
				
				case_note = CaseNote(case=case, author=player, note=case_description)
				case_note.save()
				
				return HttpResponseRedirect('../show/' + case.id_string + '/')
			
			except KeyError:
				error_message = "You gave an invalid timezone. You bad boy, you! Playing around with the POST requests..."
			except pytz.UnknownTimeZoneError:
				error_message = "There was an error with the time zones. This should never happen. Please report this."
			except ValueError: # There was an invalid weekday name or an invalid hour
				error_message = "An invalid timetable was given. This should never happen if you're not messing around with me! You're not messing around with me, are you?"
			except:
				error_message = "An internal unknown error occurred. This should never happen. Please report this."
				raise
			
		else:
			error_message = "There was an error filling out the form"
			#return HttpResponse(error_message)

	form = NewCaseForm()
	
	t = loader.get_template('cases/new.html')
	c = RequestContext(request, { 'form': form, 
								  'error_message': error_message, 
								  'punchline': get_punchline(),
								  'weekdays': ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],
								  'hours': range(24) })
	return HttpResponse(t.render(c))


# User makes a new case note
class CaseNoteForm(forms.Form):
	note = forms.CharField(max_length=4000, required=True, label="New Case Note")
	note.widget = forms.Textarea()

def new_case_note(request, case_string=''):
	try:
		case = Case.objects.get(id_string=case_string)
	except Case.DoesNotExist:
		return HttpResponse("Couldn't find case. Aborting.")
	
	form = CaseNoteForm(request.POST)
	
	if form.is_valid():
		note = form.cleaned_data['note']
		
		# Create new case note
		if request.user.is_authenticated():
			author = request.user.player
		else:
			author = case.patient
		
		case_note = CaseNote(case=case, author=author, note=note)
		case_note.save()

	return HttpResponseRedirect('../')


def logout(request):
	if request.user.is_authenticated:
		auth_logout(request)

	return HttpResponseRedirect('./')
