"""
Parse the CSM command line arguments.
"""
from argparse import ArgumentParser
import logging

from csm.calculations import permuters

logger = logging.getLogger(__name__)
import sys

from collections import namedtuple

__author__ = 'zmbq'


class OurParser(ArgumentParser):
    def error(self, message):
        print("Error: %s" % message, file=sys.stderr)
        print("Enter csm --help for help", file=sys.stderr)
        sys.exit(2)


def _create_parser():
    parser = OurParser(usage="\ncsm type input_molecule output_file [additional arguments]")

    parser.add_argument('type',
                        #choices=c_symmetries + s_symmetries + ['cs', 'ci', 'ch'],
                        help='The type of operation: cs, ci, ch, cN, sN')
    parser.add_argument('input', help='Input molecule file')
    parser.add_argument('output', default='output.txt', help='Output file')

    # Optional arguments (their names start with --)

    #types of calculations (default is exact):
    parser.add_argument('--approx', action='store_true', default=False,
                        help='use the approximate algorithm to estimate the CSM')
    parser.add_argument('--trivial', action='store_true', default=False,
                        help='CSM of identity perm, or, if chains, CSM of chain permutation with no atom permutation')
    parser.add_argument('--just-perms', action='store_true', default=False,
                        help='no calculation of CSM. without --output-perms, only counts the perm. ')


    #general input/calculation arguments:
    #parser.add_argument('--ignore-hy', action='store_true', default=False, help='Ignore Hydrogen atoms in computations')
    parser.add_argument('--remove-hy', action='store_true', default=False,
                        help='Remove Hydrogen atoms in computations, rebuild molecule without them and compute')
    parser.add_argument('--ignore-sym', action='store_true', default=False,
                        help='Ignore all atomic symbols, performing a purely geometric operation')
    parser.add_argument('--sn-max', type=int, default=8, help='The maximal sn to try, relevant only for chirality')
    parser.add_argument('--use-mass', action='store_true', default=False,
                        help='Use the atomic masses to define center of mass')
    parser.add_argument('--babel-bond', action='store_true', default=False, help='Let OpenBabel compute bonding')
    parser.add_argument('--no-babel',  action='store_true', default=False, help='force suppress automatically using OpenBabel to compute bonds')
    parser.add_argument('--use-sequence', action='store_true', default=False, help='create equivalence class for pdb file using sequence information (recommended)')


    #calculation arguments that only apply to exact:
    parser.add_argument('--use-perm', type=str, help='Compute exact CSM, for a single permutation')
    parser.add_argument('--keep-structure', action='store_true', default=False,
                        help='Maintain molecule structure from being distorted in the exact calculation')
    parser.add_argument('--no-constraint',  action='store_true', default=False,
                        help='Do not use the constraints algorithm to traverse the permutation tree')


    #calculation arguments that only apply to approx
    #parser.add_argument('--use-dir', type=str,
    #                    help='Run the approx algorithm using predefined axes as the starting point')
    parser.add_argument('--detect-outliers', action='store_true', default=False,
                        help="Use outlier detection to improve guesses for initial directions in approx algorithm")
    parser.add_argument('--use-chains', action='store_true', default=False,
                        help='Use chains specified in the PDB file in order to calculate permutations in approx or trivial algorithm')
    parser.add_argument('--no-hungarian', action='store_true', default=False,
                    help='Do not use hungarian algorithm in approx')
    parser.add_argument('--no-orthogonal', action='store_true', default=False,
                        help="Don't add orthogonal directions to calculated directions")
    parser.add_argument('--use-best-dir', action='store_true', default=False,
                    help='Only use the best direction')


    #output formatting and printing options
    parser.add_argument('--format', help='Use a specific input/output format')
    parser.add_argument('--print-norm', action='store_true', default=False,
                        help='Print the normalization factor as well')
    parser.add_argument('--print-local', action='store_true', default=False,
                        help='Print the local CSM (csm for each atom) in the output file')
    parser.add_argument('--output-perms', action='store', default=None,
                        help='Writes all enumerated permutations to file')
    parser.add_argument('--output-branches', action='store_true', default=False,
                        help='Writes all backtracking branches to the console')
    parser.add_argument('--print-approx', action='store_true', default=False,
                        help='add some printouts to approx')




    #defunct: no longer applied in code
    #parser.add_argument('--no-limit', action='store_true', default=False, help='Allows running program while ignoring computational complexity')
    #parser.add_argument('--babel-test', action='store_true', default=False, help="Test if the molecule is legal or not")
    #parser.add_argument('--time-only', action='store_true', default=False, help="Only print the time and exit")
    #parser.add_argument('--write-openu', action='store_true', default=False,
    #                    help='Write output in open university format')


    return parser



OperationCode = namedtuple('OperationCode', ('type', 'order', 'name'))
_opcode_data = {
    "cs": ('CS', 2, "MIRROR SYMMETRY"),
    "ci": ('CI', 2, "INVERSION (S2)"),
    "ch": ('CH', 2, "CHIRALITY"),
    "c2": ('CN', 2, "C2 SYMMETRY"),
    'c3': ('CN', 3, "C3 SYMMETRY"),
    'c4': ('CN', 4, "C4 SYMMETRY"),
    'c5': ('CN', 5, "C5 SYMMETRY"),
    'c6': ('CN', 6, "C6 SYMMETRY"),
    'c7': ('CN', 7, "C7 SYMMETRY"),
    'c8': ('CN', 8, "C8 SYMMETRY"),
    'c10': ('CN', 10, "C10 SYMMETRY"),
    's1':('CS', 2, "MIRROR SYMMETRY (S1)"),
    's2': ('SN', 2, "S2 SYMMETRY"),
    's4': ('SN', 4, "S4 SYMMETRY"),
    's6': ('SN', 6, "S6 SYMMETRY"),
    's8': ('SN', 8, "S8 SYMMETRY"),
    's10': ('SN', 8, "S10 SYMMETRY")
}


def get_operation_data(opcode):
    """
    Returns data about an operation based on the opcode
    Args:
        opcode: c2, s4, etc...

    Returns:
        And OperationCode object, with type, order and name
    """
    def isint(s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    opcode = opcode.lower()
    if opcode[0]=='c' and isint(opcode[1:]):
        return OperationCode(type='CN', order=int(opcode[1:]), name=opcode.upper() + ' SYMMETRY')
    if opcode[0]=='s' and isint(opcode[1:]):
        if opcode[1:]=='1':
            data = _opcode_data[opcode.lower()]
            return OperationCode(type=data[0], order=data[1], name=data[2])
        if int(opcode[1:])%2 !=0:
            raise ValueError("SN values must be even")
        return OperationCode(type='SN', order=int(opcode[1:]), name=opcode.upper() + ' SYMMETRY')
    try:
        data = _opcode_data[opcode.lower()]
    except KeyError:
        raise
    return OperationCode(type=data[0], order=data[1], name=data[2])


def _process_arguments(parse_res):
    """
    Divides the parsed arguments (from argparse) into three dictionaries
    Args:
        parse_res: Result of argparse

    Returns:
        dictionary_args - input arguments, calculation arguments and output arguments

    """

    dictionary_args = {}

    #the first three positional arguments

    op = get_operation_data(parse_res.type)

    dictionary_args['op_type'] = op.type
    dictionary_args['op_order'] = op.order
    dictionary_args['op_name'] = op.name

    dictionary_args['in_file_name'] = parse_res.input

    dictionary_args['out_file_name'] = parse_res.output

    #optional arguments:

    #types of calculations:
    dictionary_args['calc_type'] = 'exact'
    if parse_res.approx:
        dictionary_args['calc_type'] = 'approx'
    if parse_res.just_perms:
        if parse_res.approx:
            raise ValueError("--approx and --just-perms are mutually exclusive")
        dictionary_args['calc_type'] = 'just_perms'
    if parse_res.trivial:
        if parse_res.approx:
            raise ValueError("--approx and --trivial are mutually exclusive")
        if parse_res.just_perms:
            raise ValueError("--just-perms and --trivial are mutually exclusive")
        dictionary_args['calc_type'] = 'trivial'

    #general input/calculation arguments:
    dictionary_args['sn_max'] = parse_res.sn_max
    #dictionary_args['ignore_hy'] = parse_res.ignore_hy
    dictionary_args['remove_hy'] = parse_res.remove_hy
    dictionary_args['ignore_symm'] = parse_res.ignore_sym
    dictionary_args['use_sequence']= parse_res.use_sequence
    #if parse_res.use_sequence and parse_res.keep_structure:
    #    raise ValueError("--keep-structure and --use-sequence are mutually exclusive")


    #calculation arguments for exact only:
    if dictionary_args['calc_type'] == 'approx' and parse_res.keep_structure:
        logger.warning("--keep-structure cannot be used in approx calculation. --keep-structure will be ignored")
    dictionary_args['keep_structure'] = dictionary_args['keep_structure']= parse_res.keep_structure
    dictionary_args['no_constraint']=parse_res.no_constraint
    dictionary_args['babel_bond'] = parse_res.babel_bond
    dictionary_args['no_babel'] = parse_res.no_babel
    dictionary_args['use_mass'] = parse_res.use_mass

    #calculation arguments for approx only:
    if dictionary_args['calc_type'] != 'approx' and parse_res.detect_outliers:
        logger.warning("--detect-outliers applies only to approx calculation. --detect-outliers will be ignored")
    dictionary_args['detect_outliers'] = parse_res.detect_outliers

    if dictionary_args['calc_type'] != 'approx' and parse_res.no_hungarian:
        logger.warning("--no-hungarian applies only to approx calculation. --no-hungarian will be ignored")
    dictionary_args['hungarian'] = not parse_res.no_hungarian

    dictionary_args['get_orthogonal'] = not parse_res.no_orthogonal
    dictionary_args['use_best_dir'] = parse_res.use_best_dir

    #if parse_res.use_dir:
    #    if dictionary_args['calc_type'] != 'approx':
    #        logger.warning("--use-dir applies only to approx calculation. --use-dir will be ignored")
    #    dictionary_args['dir_file_name'] = parse_res.use_dir


    #TODO: Actually, use-chains could apply to several other calculation types. just hasn't been implemented yet.
    #(it already applies to trivial)
    dictionary_args['use_chains'] = dictionary_args['use_chains'] = parse_res.use_chains



    #output arguments:
    dictionary_args['print_approx']= parse_res.print_approx
    dictionary_args['print_perms'] = parse_res.output_perms
    dictionary_args['print_branches'] = parse_res.output_branches
    dictionary_args['format'] = parse_res.format
    dictionary_args['useformat'] = dictionary_args['format'] is not None
    if not dictionary_args['format']:
        # get input file extension
        dictionary_args['format'] = parse_res.input.split(".")[-1]
    if parse_res.use_perm:
        if dictionary_args['calc_type'] != 'exact':
            logger.warning("--use-perm applies only to exact calculation. --use-perm will be ignored")
        dictionary_args['perm_file_name'] = parse_res.use_perm


    # dictionary_args['write_openu'] = parse_res.write_openu
    dictionary_args['print_norm'] = parse_res.print_norm
    dictionary_args['print_local'] = dictionary_args['calc_local'] = parse_res.print_local

    dictionary_args['perms_csv_name'] = parse_res.output_perms

    permuters.print_branches = parse_res.output_branches


    return dictionary_args


def get_split_arguments(args):
    """
    :param args:
    :return:
    """
    parser = _create_parser()
    parsed_args = parser.parse_args(args)
    dictionary_args = _process_arguments(parsed_args)
    return dictionary_args
