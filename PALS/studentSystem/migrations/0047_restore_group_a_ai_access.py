from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("studentSystem", "0046_merge_20260314_1259"),
    ]

    operations = [
        migrations.AlterField(
            model_name="profile",
            name="user_type",
            field=models.CharField(
                choices=[("A", "Group A"), ("B", "Group B")],
                default="B",
                max_length=1,
            ),
        ),
    ]
