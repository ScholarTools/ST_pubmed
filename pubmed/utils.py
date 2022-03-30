# -*- coding: utf-8 -*-
"""
"""


def string_to_pmid_list(input_string:str):
    """

    Parameters
    ----------
    input_string : str


    input_string = '''
        8330046
        8149174
        8912442
        9705549
        10647690
        11746546


        26509358
        26872575
        27819757
        '''

    output = utils.string_to_pmid_list(input_string)

    """
    output = []
    for x in input_string.splitlines():
        x_stripped = x.strip()
        if x_stripped and not x_stripped.startswith('10.'):
            output.append(x_stripped)

    return output

class _Quotes(str):
    pass

def quotes(input_value):
    if input_value is None:
        return None
    elif isinstance(3,int):
        return input_value
    else:
        return _Quotes(input_value)

def display_class(class_instance,pv):
    
    return '\n%s:\n\n' % type(class_instance) + property_values_to_string(pv,extra_indentation=4)

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
    values = ['"%s"' %x if isinstance(x,_Quotes) else x for x in values]

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


def get_truncated_display_string(input_string:str, max_length:int=30):
    """

    :param input_string:
    :param max_length:
    :return:
    """
    if input_string is None:
        return 'None'
    elif len(input_string) > max_length:
        return input_string[:max_length] + '...'
    else:
        return input_string