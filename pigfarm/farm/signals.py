from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Piglet, Sow

@receiver(post_save, sender=Piglet)
@receiver(post_delete, sender=Piglet)
def update_sow_piglet_data(sender, instance, **kwargs):
    """Automatically updates the total piglet count and birth count for the sow."""
    if instance.sow:
        print(f"Signal triggered for Sow {instance.sow.name}. Updating birth count...")
        instance.sow.update_piglet_count()




@receiver([post_save, post_delete], sender=Sow)
def update_room_pig_count_sow(sender, instance, **kwargs):
    if instance.room:
        instance.room.update_pig_count()