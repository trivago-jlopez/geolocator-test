"""
Geospatial computations.
"""
import geopy
import geopy.distance


def bounding_box(point : dict, buffer_size):
    """
    Computes the bounding box around a point by buffer_size (unit: meters).
    """
    start = geopy.Point(**point)
    translate = geopy.distance.VincentyDistance(meters=100000)

    return {
        'north': translate.destination(point=start, bearing=0).latitude,
        'south': translate.destination(point=start, bearing=180).latitude,
        'east': translate.destination(point=start, bearing=90).longitude,
        'west': translate.destination(point=start, bearing=270).longitude
    }


def distance_geocodes(p1: dict, p2 : dict):
    """
    Computes the distance in meters between two point.
    """
    return geopy.distance.vincenty(geopy.Point(**p1), geopy.Point(**p2)).meters

