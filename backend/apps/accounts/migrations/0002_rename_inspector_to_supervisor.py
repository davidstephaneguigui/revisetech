from django.db import migrations


def rename_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name='Inspecteur').update(name='Superviseur')

def reverse_rename(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name='Superviseur').update(name='Superviseur')

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'), # Adapte le numéro si besoin
    ]

    operations = [
        migrations.RunPython(rename_group, reverse_rename),
    ]