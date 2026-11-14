from django.db import migrations


def merge_roles(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    regulator_group, _ = Group.objects.get_or_create(name='Régulateur')
    old_groups = Group.objects.filter(name__in=['Référent', 'Superviseur'])
    for group in old_groups:
        for user in group.user_set.all():
            user.groups.add(regulator_group)
        group.delete()

class Migration(migrations.Migration):
    dependencies = [
        ('regulation', '0001_initial'), # Dépend du fichier généré à l'étape 2
        ('auth', '0012_alter_user_first_name_max_length'),
    ]
    operations = [
        migrations.RunPython(merge_roles),
    ]