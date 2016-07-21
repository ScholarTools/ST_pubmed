# -*- coding: utf-8 -*-
"""
"""

def display_class(class_instance,pv):
    
    #Do we want to to specify the full path to the class ...?
    return '%s:\n' % type(class_instance) + property_values_to_string(pv,extra_indentation=4)

def property_values_to_string(pv,extra_indentation = 0):
    """
    Parameters
    ----------
    pv : OrderedDict
        Keys are properties, values are values
    """

    # Max length

    keys = pv[::2]
    values = pv[1::2]

    key_lengths = [len(x) for x in keys]
    max_key_length = max(key_lengths) + extra_indentation
    space_padding = [max_key_length - x for x in key_lengths]
    key_display_strings = [' ' * x + y for x, y in zip(space_padding, keys)]

    str = u''
    for (key, value) in zip(key_display_strings, values):
        str += '%s: %s\n' % (key, value)

    return str


def get_list_class_display(value):
    """
    TODO: Go from a list of objects to:
    [class name] len(#)
    """
    if value is None:
        return 'None'
    elif isinstance(value, list):
        # Check for 0 length
        try:
            if len(value) == 0:
                return u'[??] len(0)'
            else:
                return u'[%s] len(%d)' % (value[0].__class__.__name__, len(value))
        except:
            import pdb
            pdb.set_trace()
            # run the code
    else:
        return u'<%s>' % (value.__class__.__name__)


def get_truncated_display_string(input_string, max_length=50):
    if input_string is None:
        return 'None'
    elif len(input_string) > max_length:
        return input_string[:max_length] + '...'
    else:
        return input_string