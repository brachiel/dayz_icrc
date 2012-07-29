from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.core.exceptions import ValidationError
import datetime
import pytz

import dayz_icrc.settings as settings

import hashlib
import os

class Player(models.Model):
	name = models.CharField(max_length=50, unique=True)
	
	user = models.OneToOneField(User, null=True, default=None)

	TYPE_CHOICES = ((0,'Player'),(1,'Medic'))
	type = models.PositiveSmallIntegerField(choices=TYPE_CHOICES, default=0)
	
	def __unicode__(self):
		return self.name

def link_user_to_player(sender, instance, created, **kwargs):
	if created:
		try:
			player = Player.objects.get(name=instance.username)
		except Player.DoesNotExist:
			player = Player(name=instance.username, user=instance, type=1)
			player.save()
post_save.connect(link_user_to_player, sender=User)


# Makes sure the DateTime is in the first three weeks of May 2000 (May 1 is a Monday)
def validate_week_hour(value):
	if not (value.year == 2000 and value.month == 5 and 1 <= value.day and value.day <= 21):
		raise ValidationError(u"%s is not in the first three weeks of May 2000" % value)

class WeekTimeSpanManager(models.Manager):
	weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
	
	def get_datetime_by_name(self, name, tz=pytz.utc):
		day, hour = name.split("-")
		hour = int(hour)
		
		# do not use tzinfo or it will get DST wrong
		return pytz.utc.normalize(tz.localize(datetime.datetime(year=2000, month=5, day=( 8+self.weekdays.index(day) ), hour=hour)))
	
	def get_or_create_by_name(self, name, tz=None):
		if tz is not None:
			# We'll rebuild name to fit the correct name
			utctime = self.get_datetime_by_name(name, tz) 
			
			name = utctime.strftime('%a-%H') # Weekday, Hour

		try:
			return self.get(name=name)
		except WeekTimeSpan.DoesNotExist:
			return self.create_from_name(name=name)
	
	def create_from_name(self, name, tz=pytz.utc):
		"""Creates a new WeekTimeSpan object. Make sure name is already in UTC!"""
		span_from = self.get_datetime_by_name(name, tz)
		span_to = span_from + datetime.timedelta(hours=1)
		
		weektimespan = self.create(name=name, span_from=span_from, span_to=span_to)
		weektimespan.save()
		return weektimespan

class WeekTimeSpan(models.Model): # always in UTC
	name = models.CharField(max_length=40, blank=False, unique=True, editable=False)
	span_from = models.DateTimeField(validators=[validate_week_hour])
	span_to = models.DateTimeField(validators=[validate_week_hour])
	
	objects = WeekTimeSpanManager()
	
	class Meta:
		unique_together = (("span_from", "span_to"), )
	
	def __unicode__(self):
		return self.span_from.strftime("%a %H:%M - ") + self.span_to.strftime("%a %H:%M")

	def __init__(self, *args, **kwargs):
		super(WeekTimeSpan, self).__init__(*args, **kwargs)
		
		if not self.name and not self.pk:
			# If there is a 1 hour difference, we'll use a special name
			if (self.span_to - self.span_from).seconds == 60*60 and self.span_to.minute == 0 and self.span_from.minute == 0:
				self.name = self.span_from.strftime("%a-%H")
			else:
				self.name = self.__unicode__()
			


class Case(models.Model):
	id_string = models.CharField(max_length=40, blank=False, unique=True, editable=False) # holds a sha1 string that identifies this case
	
	patient = models.ForeignKey(Player, related_name="cases_as_patient")
	medics = models.ManyToManyField(Player, null=True, related_name="cases_as_medic")
	
	latitude = models.IntegerField(null=False)
	longitude = models.IntegerField(null=False)
	
	TIMEZONE_CHOICES = list(enumerate(pytz.common_timezones))
	timezone = models.PositiveSmallIntegerField(choices=TIMEZONE_CHOICES)
	meeting_times = models.ManyToManyField(WeekTimeSpan, null=True)
	
	created = models.DateTimeField(auto_now_add=True, editable=False)
	last_updated = models.DateTimeField(auto_now=True, editable=False)

	STATUS_CHOICES = ((0, 'New'), (1, 'Accepted'), (2, 'In Progress'), (3, 'Done'), (10, 'Declined'), (11, 'Failed'))
	status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, default=0)
	
	def __unicode__(self):
		return unicode(self.get_status_display() + ":" + self.patient.name + "@" + self.created.strftime("%d.%m.%y/%M:%H"))
	
	def __init__(self, *args, **kwargs):
		super(Case, self).__init__(*args, **kwargs)
		
		if not self.id_string and self.patient and not self.pk:
			self.id_string = hashlib.sha1(self.patient.name + str(self.created) + settings.SECRET_KEY + str(os.urandom(6)).encode('base64')).hexdigest()
	
	class Meta:
		permissions = (
			("edit_all_cases", "Can edit all cases, regardless if assigned or not."),
		)

class CaseNote(models.Model):
	author = models.ForeignKey(Player)
	case = models.ForeignKey(Case)
	note = models.CharField(max_length=4000, blank=True, null=False)
	
	created = models.DateTimeField(auto_now_add=True, editable=False)

	STATUS_CHOICES = Case.STATUS_CHOICES
	new_status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, null=True, default=None)
	
	def __unicode__(self):
		return self.author.name + ": " + self.note[:30]

