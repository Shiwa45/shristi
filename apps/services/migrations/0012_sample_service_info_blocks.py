from django.db import migrations


def add_sample_info_block(apps, schema_editor):
    StaticProduct = apps.get_model('services', 'StaticProduct')
    ServiceInfoBlock = apps.get_model('services', 'ServiceInfoBlock')

    product = StaticProduct.objects.filter(name__iexact='Standard Business Card').first()
    if not product:
        return

    if ServiceInfoBlock.objects.filter(product=product, title__iexact='How to Order').exists():
        return

    ServiceInfoBlock.objects.create(
        product=product,
        title='How to Order',
        body='Choose your options, upload your artwork, and place the order in minutes.',
        bullet_points='Select printing side, corner style, lamination, and quantity.\n'
                      'Upload your design file (PDF, AI, CDR).\n'
                      'Review and submit your order.',
        is_active=True,
        order=1,
    )

    ServiceInfoBlock.objects.create(
        product=product,
        title='FAQs',
        body='Common questions about our Standard Business Cards.',
        bullet_points='What is the minimum order? 200 pieces.\n'
                      'Can I print both sides? Yes.\n'
                      'Do you offer design support? Yes, on request.',
        is_active=True,
        order=2,
    )


def remove_sample_info_block(apps, schema_editor):
    StaticProduct = apps.get_model('services', 'StaticProduct')
    ServiceInfoBlock = apps.get_model('services', 'ServiceInfoBlock')

    product = StaticProduct.objects.filter(name__iexact='Standard Business Card').first()
    if not product:
        return

    ServiceInfoBlock.objects.filter(product=product, title__in=['How to Order', 'FAQs']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0011_service_info_block'),
    ]

    operations = [
        migrations.RunPython(add_sample_info_block, remove_sample_info_block),
    ]
