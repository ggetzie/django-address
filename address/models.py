from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.fields.related import ForeignObject
try:
    from django.db.models.fields.related_descriptors import ForwardManyToOneDescriptor
except ImportError:
    from django.db.models.fields.related import ReverseSingleRelatedObjectDescriptor as ForwardManyToOneDescriptor
from django.utils.encoding import python_2_unicode_compatible

import logging
logger = logging.getLogger(__name__)

# Python 3 fixes.
import sys
if sys.version > '3':
    long = int
    basestring = (str, bytes)
    unicode = str

__all__ = ['Country', 'State', 'Locality', 'Address', 'AddressField', 'Admin2',
           'Admin3', 'Admin4', 'Admin5', 'SubLocality1', 'SubLocality2',
           'SubLocality3', 'SubLocality4', 'SubLocality5', 'PostalCode',
           'PostalCodeSuffix', 'Neighborhood', 'Airport']

class InconsistentDictError(Exception):
    pass

def _to_python(value):
    raw = value.get('raw', '')
    country = value.get('country', '')
    country_code = value.get('country_code', '')
    state = value.get('state', '')
    state_code = value.get('state_code', '')
    locality = value.get('locality', '')

    if 'sublocality_level_1' in value:
        sublocality1 = value.get('sublocality_level_1', '')
    else:
        sublocality1 = value.get('sublocality', '')
        
    sublocality2 = value.get('sublocality_level_2', '')
    sublocality3 = value.get('sublocality_level_3', '')
    sublocality4 = value.get('sublocality_level_4', '')
    sublocality5 = value.get('sublocality_level_5', '')
    admin2 = value.get('admin2', '')
    admin3 = value.get('admin3', '')
    admin4 = value.get('admin4', '')
    admin5 = value.get('admin5', '')
    colloquial_area = value.get('colloquial_area', '')
    airport = value.get('airport', '')
    neighborhood = value.get('neighborhood', '')
    intersection = value.get('intersection', '')
    postal_code = value.get('postal_code', '')
    street_number = value.get('street_number', '')
    route = value.get('route', '')
    formatted = value.get('formatted', '')
    latitude = value.get('latitude', None)
    longitude = value.get('longitude', None)

    # If there is no value (empty raw) then return None.
    if not raw:
        return None

    # We need a country at the very least
    if not country and country_code:
        raise InconsistentDictError

    # Handle the country.
    # truncate country codes that are too long, this shouldn't be an issue
    # with data returned from google maps
    country_code = country_code[:2].upper()
    country_obj, new_country = Country.objects.\
                               get_or_create(name=country,
                                             code=country_code)

    # Handle the state.
    # again truncate too long codes
    state_obj = None
    if state and state_code:
        state_code = state_code[:2].upper()
        state_obj, new_state = State.objects.\
                               get_or_create(name=state,
                                             code=state_code,
                                             country=country_obj)
    # Handle postal codes
    pc_obj = None
    if postal_code:
        pc_obj, pc_new = PostalCode.objects.\
                         get_or_create(code=postal_code,
                                       country=country_obj)

    pcs_obj = None
    if pc_obj and postal_code_suffix:
        pcs_obj, pcs_new = PostalCodeSuffix.\
                           objects.\
                           get_or_create(suffix=postal_code_suffix,
                                         postal_code=pc_obj)

    # Handle administrative areas
    admin2_obj = None
    admin3_obj = None
    admin4_obj = None
    admin5_obj = None

    if admin2:
        admin2_obj, admin2_new = Admin2.objects.get_or_create(name=admin2,
                                                              state=state_obj)
    if admin2_obj and admin3:
        admin3_obj, admin3_new = Admin3.objects.get_or_create(name=admin3,
                                                              state=state_obj,
                                                              parent=admin2_obj)
    if admin3_obj and admin4:
        admin4_obj, admin4_new = Admin4.objects.get_or_create(name=admin4,
                                                              parent=admin3_obj)

    if admin4_obj and admin5:
        admin5_obj, admin5_new = Admin5.objects.get_or_create(name=admin5,
                                                              parent=admin4_obj)
        
        
    # Handle the locality and sublocalities.
    locality_obj = None
    sublocality1_obj = None
    sublocality2_obj = None
    sublocality3_obj = None
    sublocality4_obj = None
    sublocality5_obj = None
    
    if locality:
        locality_obj, lo_new = Locality.objects.get_or_create(name=locality,
                                                              state=state_obj)
    if sublocality1:
        sublocality1_obj, sl1_new = SubLocality1.objects.\
                                    get_or_create(name=sublocality1,
                                                  locality=locality_obj,
                                                  admin2=admin2_obj,
                                                  state=state_obj)
    if sublocality2 and sublocality1_obj:
        sublocality2_obj, sl2_new = SubLocality2.objects.\
                                    get_or_create(name=sublocality2,
                                                  parent=sublocality1_obj)

    if sublocality3 and sublocality2_obj:
        sublocality3_obj, sl3_new = SubLocality3.objects.\
                                    get_or_create(name=sublocality3,
                                                  parent=sublocality2_obj)

    if sublocality4 and sublocality3_obj:
        sublocality4_obj, sl4_new = SubLocality4.objects.\
                                     get_or_create(name=sublocality4,
                                                   parent=sublocality3_obj)

    if sublocality5 and sublocality4_obj:
        sublocality5_obj, sl5_new = SubLocality5.objects.\
                                    get_or_create(name=sublocality5,
                                                  parent=sublocality4_obj)

    # Handle airport, neighborhood
    airport_obj = None
    if airport:
        airport_obj, ap_new = Airport.objects.get_or_create(name=airport)

    neighborhood_obj = None
    if neighborhood and locality_obj:
        neighborhood_obj, nh_new = Neighborhood.objects.\
                                   get_or_create(name=Neighborhood,
                                                 locality=locality_obj)


    addr, addr_new = Address.objects.get_or_create(raw=raw)
    
    # if address exists, add in any missing parts
    if not addr_new:
        if street_number and not addr.street_number:
            addr.street_number = street_number
            
        if route and not addr.route:
            addr.route = route

        if locality_obj and not addr.locality:
            addr.locality = locality_obj

        if sublocality1_obj and not addr.sublocality1:
            addr.sublocality1 = sublocality1_obj

        if sublocality2_obj and not addr.sublocality2:
            addr.sublocality2 = sublocality2_obj

        if sublocality3_obj and not addr.sublocality3:
            addr.sublocality3 = sublocality3_obj

        if sublocality4_obj and not addr.sublocality4:
            addr.sublocality4 = sublocality4_obj

        if sublocality5_obj and not addr.sublocality5:
            addr.sublocality5 = sublocality5_obj

        if admin2_obj and not addr.admin2:
            addr.admin2 = admin2_obj

        if admin3_obj and not addr.admin3:
            addr.admin3 = admin3_obj

        if admin4_obj and not addr.admin4:
            addr.admin4 = admin4_obj

        if admin5_obj and not addr.admin5:
            addr.admin5 = admin5_obj

        if state_obj and not addr.state:
            addr.state = state_obj

        if pc_obj and not addr.postal_code:
            addr.postal_code = pc_obj

        if pcs_obj and not addr.postal_code_suffix:
            addr.postal_code_suffix = pcs_obj            

        if country_obj and not addr.country:
            addr.country = country_obj

        if formatted and not addr.formatted:
            addr.formatted = formatted

        if latitude and not addr.latitude:
            addr.latitude = latitude

        if longitude and not addr.longitude:
            addr.longitude = longitude

        if colloquial_area and not addr.colloquial_area:
            addr.colloquial_area = colloquial_area

        if neighborhood_obj and not addr.neighborhood:
            addr.neighborhood = neighborhood_obj

        if airport_obj and not addr.airport:
            addr.airport = airport_obj

        addr.save()
            
    # Done.
    return addr

def to_python(value):
    """
    Convert a dictionary to an Address object
    """

    # Keep `None`s.
    if value is None:
        return None

    # Is it already an address object?
    if isinstance(value, Address):
        return value

    # If we have an integer, assume it is a model primary key. This is mostly for
    # Django being a cunt.
    elif isinstance(value, (int, long)):
        return value

    # A string is considered a raw value.
    elif isinstance(value, basestring):
        obj = Address(raw=value)
        obj.save()
        return obj

    # A dictionary of named address components.
    elif isinstance(value, dict):

        # Attempt a conversion.
        try:
            return _to_python(value)
        except InconsistentDictError:
            return Address.objects.create(raw=value['raw'])

    # Not in any of the formats I recognise.
    raise ValidationError('Invalid address value.')

@python_2_unicode_compatible
class Country(models.Model):
    name = models.CharField(max_length=40, unique=True)
    
    # code not unique as there are duplicates (IT)
    code = models.CharField(max_length=2, blank=True, default="") 

    class Meta:
        verbose_name_plural = 'Countries'
        ordering = ('name',)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class State(models.Model):
    """
    Google maps address component - administrative_area_level_1
    State in the United States
    """
    name = models.CharField(max_length=165)
    code = models.CharField(max_length=3, blank=True)
    country = models.ForeignKey(Country, related_name='states',
                                on_delete=models.CASCADE)

    class Meta:
        unique_together = ('name', 'country')
        ordering = ('country', 'name')

    def __str__(self):
        return "{}, {}".format(self.name, self.country)

    def to_str(self):
        return '%s'%(self.name or self.code)

###
### County
###
@python_2_unicode_compatible
class Admin2(models.Model):
    """
    Google maps address component - administrative_area_level_2
    In the US, this corresponds to a county. 
    """
    name = models.CharField(max_length=165, blank=True, default="")
    state = models.ForeignKey(State, related_name='counties',
                              on_delete=models.CASCADE)

    class Meta:
        unique_together = ('name', 'state')
        ordering = ('state', 'name')

    def __str__(self):
        txt = "{} - {}, {}".format(self.name,
                                   self.state.name,
                                   self.state.country.name)
        return txt

###
### Admin 3 - unincorporated area
###
@python_2_unicode_compatible
class Admin3(models.Model):
    """
    Google maps address component - administrative_area_level_3
    In the US, this is an unincorporated area or township. 
    Used in place of locality  when unavailable.
    """
    name = models.CharField(max_length=165)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    parent = models.ForeignKey(Admin2, blank=True, null=True,
                               on_delete=models.CASCADE)

    class Meta:
        unique_together = ('name', 'state')
        ordering = ('state', 'parent', 'name')

    def __str__(self):
        txt = "{}, {} - {}".format(name, state.code, country.name)
        return txt


@python_2_unicode_compatible
class Admin4(models.Model):
    """
    Google maps address component - administrative_area_level_4
    """
    name = models.CharField(max_length=165)
    parent = models.ForeignKey(Admin3, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('name', 'parent')
        ordering = ('parent', 'name')

    def __str__(self):
        return "{}, {}".format(self.name, self.parent)


@python_2_unicode_compatible
class Admin5(models.Model):
    """
    Google maps address component - administrative_area_level_5
    """
    name = models.CharField(max_length=165)
    parent = models.ForeignKey(Admin4, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('name', 'parent')
        ordering = ('parent', 'name')

    def __str__(self):
        return "{}, {}".format(self.name, self.parent)


##
## A locality (suburb).
##
@python_2_unicode_compatible
class Locality(models.Model):
    """ Google maps address component - locality"""
    name = models.CharField(max_length=165)
    state = models.ForeignKey(State, related_name='localities',
                              on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = 'Localities'
        unique_together = ('name', 'state')
        ordering = ('state', 'name')

    def __str__(self):
        return "{}, {} {}".format(self.name, self.state.name,
                                  self.state.country.name)

class SubLocality1(models.Model):
    """ Google maps address component - sublocality or sublocality_level_1"""
    name = models.CharField(max_length=165)
    locality = models.ForeignKey(Locality, on_delete=models.SET_NULL,
                                 blank=True, null=True)
    admin2 = models.ForeignKey(Admin2, on_delete=models.SET_NULL,
                               blank=True, null=True)
    state = models.ForeignKey(State, on_delete=models.CASCADE,
                              blank=True, null=True)

    class Meta:
        unique_together = ('name', 'locality')
        ordering = ('name', 'locality')

    def __str__(self):
        return "{}, {}".format(self.name, self.locality)

    
class SubLocality2(models.Model):
    """ Google maps address component - sublocality_level_2"""
    name = models.CharField(max_length=165)
    parent = models.ForeignKey(SubLocality1, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('name', 'parent')
        ordering = ('parent', 'name')

    def __str__(self):
        return "{}, {}".format(self.name, self.parent)


class SubLocality3(models.Model):
    """ Google maps address component - sublocality_level_3"""
    name = models.CharField(max_length=165)
    parent = models.ForeignKey(SubLocality2, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('name', 'parent')
        ordering = ('parent', 'name')

    def __str__(self):
        return "{}, {}".format(self.name, self.parent)

    
class SubLocality4(models.Model):
    """ Google maps address component - sublocality_level_4"""
    name = models.CharField(max_length=165)
    parent = models.ForeignKey(SubLocality3, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('name', 'parent')
        ordering = ('parent', 'name')    

    def __str__(self):
        return "{}, {}".format(self.name, self.parent)


###
### sublocality level 5
###    
class SubLocality5(models.Model):
    """ Google maps address component - sublocality_level_5"""
    name = models.CharField(max_length=165)
    parent = models.ForeignKey(SubLocality4, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('name', 'parent')
        ordering = ('parent', 'name')    

    def __str__(self):
        return "{}, {}".format(self.name, self.parent)


class Neighborhood(models.Model):

    name = models.CharField(max_length=165)
    locality = models.ForeignKey(Locality, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('name', 'locality')
        ordering = ('locality', 'name')

    def __str__(self):
        return "{}, {}".format(self.name, self.locality)


class Airport(models.Model):
    name = models.CharField(max_length=165, unique=True)

    def __str__(self):
        return self.name


class PostalCode(models.Model):
    code = models.CharField(max_length=15)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('code', 'country')
        ordering = ('country', 'code')

    def __str__(self):
        return "{} - {}".format(self.code, self.country)


class PostalCodeSuffix(models.Model):
    suffix = models.CharField(max_length=15)
    code = models.ForeignKey(PostalCode, on_delete=models.CASCADE)

    class Meta:
        unique_together =  ('suffix', 'code')
        ordering = ('code', 'suffix')

    def __str__(self):
        return "{}-{}".format(self.code, self.suffix)

    
##
## An address. If for any reason we are unable to find a matching
## decomposed address we will store the raw address string in `raw`.
##
@python_2_unicode_compatible
class Address(models.Model):
    street_number = models.CharField(max_length=20, blank=True, default="")
    route = models.CharField(max_length=100, blank=True, default="")
    locality = models.ForeignKey(Locality, related_name='addresses',
                                 blank=True, null=True,
                                 on_delete=models.CASCADE)
    
    sublocality1 = models.ForeignKey(SubLocality1, blank=True, null=True,
                                     related_name='sl1_addresses',
                                     on_delete=models.SET_NULL)
    
    sublocality2 = models.ForeignKey(SubLocality2, blank=True, null=True,
                                     related_name='sl2_addresses',
                                     on_delete=models.SET_NULL)

    sublocality3 = models.ForeignKey(SubLocality3, blank=True, null=True,
                                     related_name='sl3_addresses',
                                     on_delete=models.SET_NULL)

    sublocality4 = models.ForeignKey(SubLocality4, blank=True, null=True,
                                     related_name='sl4_addresses',
                                     on_delete=models.SET_NULL)

    sublocality5 = models.ForeignKey(SubLocality1, blank=True, null=True,
                                     related_name='sl5_addresses',
                                     on_delete=models.SET_NULL)

    admin2 = models.ForeignKey(Admin2, blank=True, null=True,
                               related_name='adm2_addresses',
                               on_delete=models.CASCADE)

    admin3 = models.ForeignKey(Admin3, blank=True, null=True,
                               related_name='adm3_addresses',
                               on_delete=models.CASCADE)

    admin4 = models.ForeignKey(Admin4, blank=True, null=True,
                               related_name='adm4_addresses',
                               on_delete=models.SET_NULL)

    admin5 = models.ForeignKey(Admin5, blank=True, null=True,
                               related_name='adm5_addresses',
                               on_delete=models.SET_NULL)

    state = models.ForeignKey(State, blank=True, null=True,
                              on_delete = models.SET_NULL)
    
    postal_code = models.ForeignKey(PostalCode, on_delete=models.CASCADE,
                                    related_name='pc_addresses',
                                    blank=True, null=True)

    postal_code_suffix = models.ForeignKey(PostalCodeSuffix,
                                           related_name='pcs_addresses',
                                           blank=True,
                                           null=True,
                                           on_delete=models.SET_NULL)

    country = models.ForeignKey(Country, blank=True, null=True,
                                on_delete=models.SET_NULL)
    
    raw = models.CharField(max_length=200, unique=True)
    formatted = models.CharField(max_length=200, blank=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    intersection = models.CharField(max_length=165, blank=True,
                                    default="")
    
    colloquial_area = models.CharField(max_length=165, blank=True,
                                       default="")
    
    neighborhood = models.ForeignKey(Neighborhood, blank=True,
                                     null=True, on_delete=models.SET_NULL)
    
    airport = models.ForeignKey(Airport, blank=True, null=True,
                                on_delete=models.SET_NULL)
    

    


    class Meta:
        verbose_name_plural = 'Addresses'
        ordering = ('locality', 'route', 'street_number')
        # unique_together = ('locality', 'route', 'street_number')

    def __str__(self):
        if self.formatted:
            return self.formatted
        else:
            return self.raw

    def clean(self):
        if not self.raw:
            raise ValidationError('Addresses may not have a blank `raw` field.')

    def as_dict(self):
        ad = dict(
            street_number = self.street_number,
            route = self.route,
            locality = self.locality or '',
            sublocality_level_1 = self.sublocality1 or '',
            sublocality_level_2 = self.sublocality2 or '',
            sublocality_level_3 = self.sublocality3 or '',
            sublocality_level_4 = self.sublocality4 or '',
            sublocality_level_5 = self.sublocality5 or '',
            state = self.state or '',
            administrative_area_level_1 = self.state,
            administrative_area_level_2 = self.admin2 or '',
            administrative_area_level_3 = self.admin3 or '',
            administrative_area_level_4 = self.admin4 or '',
            administrative_area_level_5 = self.admin5 or '',
            country = self.country or '',
            raw=self.raw,
            formatted=self.formatted,
            latitude=self.latitude or '',
            longitude=self.longitude or '',
            intersection = self.intersection,
            airport = self.airport or '',
            neighborhood = self.neighborhood or '',
            colloquial_area = self.colloquial_area,
        )
        return ad

class AddressDescriptor(ForwardManyToOneDescriptor):

    def __set__(self, inst, value):
        super(AddressDescriptor, self).__set__(inst, to_python(value))

##
## A field for addresses in other models.
##
class AddressField(models.ForeignKey):
    description = 'An address'

    def __init__(self, *args, **kwargs):
        kwargs['to'] = 'address.Address'
        super(AddressField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name, virtual_only=False):
        super(ForeignObject, self).contribute_to_class(cls, name)
        setattr(cls, self.name, AddressDescriptor(self))

    # def deconstruct(self):
    #     name, path, args, kwargs = super(AddressField, self).deconstruct()
    #     del kwargs['to']
    #     return name, path, args, kwargs

    def formfield(self, **kwargs):
        from .forms import AddressField as AddressFormField
        defaults = dict(form_class=AddressFormField)
        defaults.update(kwargs)
        return super(AddressField, self).formfield(**defaults)
