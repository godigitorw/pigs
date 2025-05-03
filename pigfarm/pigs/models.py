# pigs/models.py
from django.db import models
from farm.models import Room

class Pig(models.Model):
    name = models.CharField(max_length=20)
    room = models.ForeignKey(Room, related_name='pigs', on_delete=models.SET_NULL, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        """Update pig count when pig is added to a room."""
        super().save(*args, **kwargs)
        if self.room:
            self.room.update_pig_count()

    def delete(self, *args, **kwargs):
        """Update pig count when pig is removed from a room."""
        room = self.room
        super().delete(*args, **kwargs)
        if room:
            room.update_pig_count()

    def __str__(self):
        return self.name