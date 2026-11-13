from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.pedagogy.models import Sequence


class Command(BaseCommand):
    help = 'Archives sequence drafts older than 90 days without any sessions.'

    def handle(self, *args, **kwargs):
        # Calculate the cutoff date (3 months = approx. 90 days)
        cutoff_date = timezone.now() - timedelta(days=90)
        
        # Find draft sequences created before the cutoff date that have no sessions generated yet
        # (meaning the intention was never validated, or the skeleton wasn't created)
        old_drafts = Sequence.objects.filter(
            status='DRAFT',
            created_at__lt=cutoff_date,
            sessions__isnull=True 
        ).distinct()
        
        count = old_drafts.count()
        
        if count > 0:
            # Update the status to ARCHIVED
            old_drafts.update(status='ARCHIVED')
            self.stdout.write(self.style.SUCCESS(f'Successfully archived {count} draft sequence(s).'))
        else:
            self.stdout.write(self.style.SUCCESS('No draft sequences needed archiving today.'))