from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_site_settings'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='services_video_url',
            field=models.URLField(blank=True, help_text='Single video URL used on service pages'),
        ),
        migrations.AddField(
            model_name='sitesetting',
            name='services_video_poster',
            field=models.ImageField(blank=True, null=True, upload_to='site/'),
        ),
    ]
