from django.db import migrations, models


def migrate_profiles_to_group_b(apps, schema_editor):
    Profile = apps.get_model("studentSystem", "Profile")
    Profile.objects.exclude(user_type="B").update(user_type="B")


class Migration(migrations.Migration):

    dependencies = [
        ("studentSystem", "0044_alter_endsurveyresponse_ml_familiarity"),
    ]

    operations = [
        migrations.RunPython(migrate_profiles_to_group_b, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="endsurveyresponse",
            name="adaptation_quality",
        ),
        migrations.RemoveField(
            model_name="endsurveyresponse",
            name="adaptive_hint_helpfulness",
        ),
        migrations.AlterField(
            model_name="profile",
            name="user_type",
            field=models.CharField(choices=[("B", "Group B")], default="B", max_length=1),
        ),
    ]
