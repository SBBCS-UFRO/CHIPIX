# SPDX-License-Identifier: GPL-3.0-or-later
"""Validate a whole preset before applying any changes to native widgets."""
import math
from .box_geometry import BoxStyle, box_bild
from .models import SearchBox


def validate_customization(data):
    def number(value, low, high, integer=False):
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError()
        if integer and type(value) is not int:
            raise ValueError()
    def rgb(value):
        if len(value) != 3:
            raise ValueError()
        for v in value:
            number(v,0,1)
    try:
        if data['schema_version'] != 1 or data['application'] != 'CHIPIX':
            raise ValueError()
        box, style = SearchBox(**data['box']), BoxStyle(**data['style'])
        for value in box.center:
            number(value,-100000,100000)
        for value in box.size:
            number(value,.001,100000)
        for value in box.rotation:
            number(value,-180,180)
        box_bild(box, style)
        if data['background'] not in ('current','white','black','slate','custom') or data['lighting'] not in ('current','simple','soft','full','flat','default'):
            raise ValueError()
        rgb(data['background_rgb'])
        image, distances = data['image'], data['distances']
        number(image['width'],64,8192,True)
        number(image['height'],64,8192,True)
        number(image['supersample'],1,4,True)
        for key in ('transparent','box','handles','distances'):
            if type(image[key]) is not bool:
                raise ValueError()
        rgb(distances['color'])
        number(distances['radius'],.01,2)
        number(distances['dashes'],0,50,True)
        number(distances['label_size'],8,128,True)
        if type(distances['labels']) is not bool:
            raise ValueError()
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        raise ValueError('Archivo de personalización inválido o incompatible.') from error
    return data
