from django.db import migrations, models
import django.db.models.deletion


def create_default_no_design_section(apps, schema_editor):
    NoDesignSection = apps.get_model('core', 'NoDesignSection')
    NoDesignFeature = apps.get_model('core', 'NoDesignFeature')

    section = NoDesignSection.objects.create(
        title="No Design?",
        highlight_text="No Problem!",
        description=(
            "Don't have a design? Our expert design team will create stunning, "
            "professional designs tailored to your brand and requirements at no extra cost."
        ),
        cta_text="Get Free Design",
        cta_url="",
        image_static_path="img/no_design.png",
        image_alt_text="Professional Design Team",
        is_active=True,
        order=0,
    )

    features = [
        "Free Design Consultation",
        "Professional Design Team",
        "Unlimited Revisions",
        "24-Hour Design Turnaround",
    ]

    for index, text in enumerate(features):
        NoDesignFeature.objects.create(
            section=section,
            text=text,
            icon_class="fas fa-check",
            is_active=True,
            order=index,
        )


def remove_default_no_design_section(apps, schema_editor):
    NoDesignSection = apps.get_model('core', 'NoDesignSection')
    NoDesignSection.objects.filter(title="No Design?", highlight_text="No Problem!").delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_homepageslider_background_gradient_from_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='NoDesignSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(default='No Design?', max_length=200)),
                ('highlight_text', models.CharField(default='No Problem!', max_length=200)),
                ('description', models.TextField()),
                ('cta_text', models.CharField(default='Get Free Design', max_length=100)),
                ('cta_url', models.CharField(blank=True, help_text='Leave blank to use the contact page', max_length=200)),
                ('image', models.ImageField(blank=True, null=True, upload_to='home_sections/')),
                ('image_static_path', models.CharField(default='img/no_design.png', max_length=200)),
                ('image_alt_text', models.CharField(default='Professional Design Team', max_length=200)),
                ('is_active', models.BooleanField(default=True)),
                ('order', models.IntegerField(default=0, help_text='Display order')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'No Design Section',
                'verbose_name_plural': 'No Design Sections',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='NoDesignFeature',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=200)),
                ('icon_class', models.CharField(default='fas fa-check', max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('order', models.IntegerField(default=0)),
                ('section', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='features', to='core.nodesignsection')),
            ],
            options={
                'verbose_name': 'No Design Feature',
                'verbose_name_plural': 'No Design Features',
                'ordering': ['order'],
            },
        ),
        migrations.RunPython(create_default_no_design_section, remove_default_no_design_section),
    ]
