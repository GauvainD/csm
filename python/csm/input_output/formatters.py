import math
import sys

def format_perm_count(num):
    if abs(num) < 1000000:
        return '%d' % num
    return '%.5g' % num

def format_CSM(num):
    return "%.4lf" % (abs(num))

def non_negative_zero(number):
    if math.fabs(number)<0.00001:
        return 0.0000
    else:
        return number


def csm_log(*strings, **kwargs):
    print(*strings, **kwargs, file=sys.stderr)