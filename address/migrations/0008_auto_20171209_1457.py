# Generated by Django 2.0 on 2017-12-09 14:57
import re
from django.db import migrations

def addr_postal(apps, schema_editor):
    zip4 = re.compile(r'\d{5}-\d{4}')
    Address = apps.get_model('address', 'Address')
    PostalCode  = apps.get_model('address', 'PostalCode')
    PostalCodeSuffix = apps.get_model('address', 'PostalCodeSuffix')

    for addr in Address.objects.all():
        if not addr.locality: continue
        codestr = addr.locality.postal_code
        if not codestr: continue
        country = addr.locality.state.country
        if (country.code == 'US' and zip4.match(codestr)):
            parts = codestr.split('-')
            code, code_new = PostalCode.objects.\
                             get_or_create(code=parts[0],
                                           country=country)
            
            suff, suff_new = PostalCodeSuffix.objects.\
                             get_or_create(suffix=parts[1],
                                           code=code)
            addr.postal_code = code
            addr.postal_code_suffix = suff
            addr.save()
        else:
            code, code_new = PostalCode.objects.\
                             get_or_create(code=codestr,
                                           country=country)
            addr.postal_code = code
            addr.save()


class Migration(migrations.Migration):

    dependencies = [
        ('address', '0007_auto_20171209_1450'),
    ]

    operations = [
        migrations.RunPython(addr_postal),
    ]