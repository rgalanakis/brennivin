"""
Functions for formatting numbers in a pretty way.

Members
=======
"""
import math as _math


# noinspection PyShadowingBuiltins
def format(num, precision):
    """
    Returns a string representation for a floating point number
    that is rounded to the given precision and displayed with
    commas and spaces.

    >>> print format(123567.0, 1000)
    124,000
    >>> print format(5.3918e-07, 1e-10)
    0.000 000 539 2

    This kind of thing is wonderful for producing tables for
    human consumption.
    """
    accpow = _math.floor(_math.log10(precision))
    if num < 0:
        digits = int(_math.fabs(num / pow(10, accpow) - 0.5))
    else:
        digits = int(_math.fabs(num / pow(10, accpow) + 0.5))
    result = ''
    if digits > 0:
        for i in range(0, int(accpow)):
            if (i % 3) == 0 and i > 0:
                result = '0,' + result
            else:
                result = '0' + result
        curpow = int(accpow)
        while digits > 0:
            adigit = chr((digits % 10) + ord('0'))
            if (curpow % 3) == 0 and curpow != 0 and len(result) > 0:
                if curpow < 0:
                    result = adigit + ' ' + result
                else:
                    result = adigit + ',' + result
            elif curpow == 0 and len(result) > 0:
                result = adigit + '.' + result
            else:
                result = adigit + result
            digits //= 10
            curpow += 1
        for i in range(curpow, 0):
            if (i % 3) == 0 and i != 0:
                result = '0 ' + result
            else:
                result = '0' + result
        if curpow <= 0:
            result = "0." + result
        if num < 0:
            result = '-' + result
    else:
        result = "0"
    return result


KB = 1024


def format_memory(val):
    """Pretty formatting of memory."""
    val = float(val)
    if val < KB:
        label = "B"
    elif KB < val < KB ** 2:
        label = "KB"
        val /= KB
    elif KB ** 2 < val < KB ** 3:
        label = "MB"
        val /= KB ** 2
    # elif val > KB**3:
    else:
        label = "GB"
        val /= KB ** 3
    return str(round(val, 2)) + label
