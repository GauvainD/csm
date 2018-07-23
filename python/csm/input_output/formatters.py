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

def format_unknown_str(input):
    try:
        num=float(input)
        if int(input)==num:
            return int(input)
        return "%.4lf" % (num)
    except:
        return str(input)

def mol_header(molecule, index=0):
    mol_index=molecule.metadata.index+1 #index from file is primary
    mol_str="%04d" % mol_index
    return mol_str


global csm_out_pipe
csm_out_pipe=sys.stdout

global output_strings
output_strings=[]

def csm_log(*strings, file=csm_out_pipe, **kwargs):
    output_strings.append(" ".join(strings))
    print(*strings, **kwargs, file=file)
