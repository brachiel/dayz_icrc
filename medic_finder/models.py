from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
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


class Case(models.Model):
	id_string = models.CharField(max_length=40, blank=False, unique=True) # holds a sha1 string that identifies this case
	
	patient = models.ForeignKey(Player, related_name="cases_as_patient")
	medics = models.ManyToManyField(Player, null=True, related_name="cases_as_medic")
	
	latitude = models.IntegerField(null=False)
	longitude = models.IntegerField(null=False)
	
	created = models.DateTimeField(auto_now_add=True)
	last_updated = models.DateTimeField(auto_now=True)

	STATUS_CHOICES = ((0, 'New'), (1, 'Accepted'), (2, 'In Progress'), (3, 'Done'), (10, 'Declined'), (11, 'Failed'))
	status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, default=0)
	
	def __unicode__(self):
		return unicode(self.get_status_display() + ":" + self.patient.name + "@" + self.created.strftime("%d.%m.%y/%M:%H"))
	
	def __init__(self, *args, **kwargs):
		super(Case, self).__init__(*args, **kwargs)
		
		if not self.id_string and self.patient and not self.pk:
			self.id_string = hashlib.sha1(self.patient.name + str(self.created) + settings.SECRET_KEY + str(os.urandom(6)).encode('base64')).hexdigest()

class CaseNote(models.Model):
	author = models.ForeignKey(Player)
	case = models.ForeignKey(Case)
	note = models.CharField(max_length=4000, blank=True, null=False)

	STATUS_CHOICES = Case.STATUS_CHOICES[1:]
	new_status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, null=True, default=None)
	
	def __unicode__(self):
		return self.author.name + ": " + self.note[:30]

