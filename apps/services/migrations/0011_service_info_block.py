from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0010_staticproduct_group_name_staticproduct_group_order'),
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceInfoBlock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('body', models.TextField(blank=True)),
                ('bullet_points', models.TextField(blank=True, help_text='One point per line')),
                ('is_active', models.BooleanField(default=True)),
                ('order', models.IntegerField(default=0)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='info_blocks', to='services.staticproduct')),
            ],
            options={
                'verbose_name': 'Service Info Block',
                'verbose_name_plural': 'Service Info Blocks',
                'ordering': ['order'],
            },
        ),
    ]
