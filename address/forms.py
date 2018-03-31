from django import forms
# from uni_form.helpers import *
from django.utils.safestring import mark_safe
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from .models import Address, to_python
import logging

# Python 3 fixes.
import sys

if sys.version > '3':
    long = int
    basestring = (str, bytes)
    unicode = str

logger = logging.getLogger(__name__)

__all__ = ['AddressWidget', 'AddressField']

if not settings.GOOGLE_API_KEY:
    raise ImproperlyConfigured("GOOGLE_API_KEY is not configured in settings.py")


class AddressWidget(forms.TextInput):
    components = [('country', 'country'),
                  ('country_code', 'country_short'),
                  ('route', 'route'),
                  ('street_number', 'street_number'),
                  ('locality', 'locality'),
                  ('sublocality', 'sublocality'),
                  ('sublocality_level_1', 'sublocality_level_1'),
                  ('sublocality_level_2', 'sublocality_level_2'),
                  ('sublocality_level_3', 'sublocality_level_3'),
                  ('sublocality_level_4', 'sublocality_level_4'),
                  ('sublocality_level_5', 'sublocality_level_5'),
                  ('postal_code', 'postal_code'),
                  ('postal_code_suffix', 'postal_code_suffix'),
                  ('state', 'administrative_area_level_1'),
                  ('state_code', 'administrative_area_level_1_short'),
                  ('admin2', 'administrative_area_level_2'),
                  ('admin3', 'administrative_area_level_3'),
                  ('admin4', 'administrative_area_level_4'),
                  ('admin5', 'administrative_area_level_5'),
                  ('colloquial_area', 'colloquial_area'),
                  ('neighborhood', 'neighborhood'),
                  ('airport', 'airport'),
                  ('intersection', 'intersection'),
                  ('formatted', 'formatted_address'),
                  ('latitude', 'lat'),
                  ('longitude', 'lng'),
                  ('pk', 'address_pk'),
                  
    ]

    @property
    def media(self):
        if self.show_map:
            addr_js = 'address/js/address_map.js'
        else:
            addr_js = 'address/js/address.js'
            
        maps_api  = ('https://maps.googleapis.com/maps/api/js?'
                     'libraries=places&key=%s') % settings.GOOGLE_API_KEY
        js = (maps_api,
              'js/jquery.geocomplete.min.js',
              addr_js)
        return forms.Media(js=js)

    

    def __init__(self, *args, **kwargs):
        attrs = kwargs.get('attrs', {})
        classes = attrs.get('class', '')
        classes += (' ' if classes else '') + 'address'
        self.show_map = kwargs.pop('show_map', False)
        attrs['class'] = classes
        kwargs['attrs'] = attrs
        super(AddressWidget, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, **kwargs):

        # Can accept None, a dictionary of values or an Address object.
        if value in (None, ''):
            logger.info('found nothing in render')
            ad = {}
        elif isinstance(value, dict):
            logger.info('found dict in render')
            ad = value
        elif isinstance(value, (int, long)):
            logger.info('found pk in render')
            ad = Address.objects.get(pk=value)
            ad = ad.as_dict()
        else:
            logger.info("found address object in render")
            # logger.info(value.as_dict())
            ad = value.as_dict()

        # Generate the elements. We should create a suite of hidden fields
        # For each individual component, and a visible field for the raw
        # input. Begin by generating the raw input.
        elems = [super(AddressWidget, self).render(name, ad.get('formatted', None), attrs, **kwargs)]

        # Now add the hidden fields.
        elems.append('<div id="%s_components">' % name)
        for com in self.components:
            elems.append('<input type="hidden" name="%s_%s" data-geo="%s" value="%s" />' % (
                name, com[0], com[1], ad.get(com[0], ''))
            )
        elems.append('</div>')
        

        return mark_safe(unicode('\n'.join(elems)))

    def value_from_datadict(self, data, files, name):
        raw = data.get(name, '')
        if not raw:
            return raw
        ad = dict([(c[0], data.get(name + '_' + c[0], '')) for c in self.components])
        ad['raw'] = raw
        return ad


class AddressField(forms.ModelChoiceField):
    widget = AddressWidget

    def __init__(self, *args, **kwargs):
        kwargs['queryset'] = Address.objects.none()
        super(AddressField, self).__init__(*args, **kwargs)

    def to_python(self, value):

        # Treat `None`s and empty strings as empty.
        if value is None or value == '':
            return None

        # Check for garbage in the lat/lng components.
        for field in ['latitude', 'longitude']:
            if field in value:
                if value[field]:
                    try:
                        value[field] = float(value[field])
                    except:
                        raise forms.ValidationError('Invalid value for %(field)s', code='invalid',
                                                    params={'field': field})
                else:
                    value[field] = None
                    
        # logger.info(f"Value of address in form:\n{value}")
        return to_python(value)
