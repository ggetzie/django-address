from ..models import Address, Locality

def dedupe():
    """
    remove duplicate localities
    """

    for addr in Address.objects.all():
        try:
            locs = Locality.objects.filter(name=addr.locality.name,
                                           state=addr.locality.state).\
                                           order_by('id')

        except Locality.DoesNotExist:
            continue
        if len(locs) == 1: continue
        if addr.locality.id > locs[0].id:
            addr.locality = locs[0]
            addr.save()
        for loc in locs[1:]:
            loc.delete()  
