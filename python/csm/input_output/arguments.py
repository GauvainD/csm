from argparse import ArgumentParser
import logging

import os

from csm.calculations import permuters
from csm.calculations.data_classes import Operation

logger = logging.getLogger(__name__)
import sys

class OurParser(ArgumentParser):
    def error(self, message):
        print("Error: %s" % message, file=sys.stderr)
        print("Enter csm --help for help", file=sys.stderr)
        sys.exit(2)

def _create_parser():
    def input_utility_func(parser):
        parser.add_argument('--remove-hy', action='store_true', default=False,
                            help='Remove Hydrogen atoms, rebuild molecule without them, and compute')
        parser.add_argument('--ignore-sym', action='store_true', default=False,
                            help='Ignore all atomic symbols, performing a purely geometric operation')
        parser.add_argument('--use-mass', action='store_true', default=False,
                            help='Use the atomic masses to define center of mass')
        parser.add_argument('--babel-bond', action='store_true', default=False,
                            help='Let OpenBabel compute bonding')
        parser.add_argument('--use-sequence', action='store_true', default=False,
                            help='create equivalence class for pdb file using sequence information.')
        parser.add_argument('--use-chains', action='store_true', default=False,
                            help='When a molecule has chains, use them (affects trivial, approx)')
        parser.add_argument('--read-fragments', action='store_true', default=False,
                            help='Read fragments from .mol or .pdb file as chains')

    def output_utility_func(parser):
        parser.add_argument('--json-output', action='store_true', default=False,
                            help='Print output in json format to a file')
        parser.add_argument('--print-local', action='store_true', default=False,
                            help='Print the local CSM (csm for each atom) in the output file')
        parser.add_argument('--print-denorm', action='store_true', default=False,
                            help='when printing the original molecule, print the denormalized coordinates')

    def shared_calc_utility_func(parser):
        parser.add_argument('type',
                            # choices=c_symmetries + s_symmetries + ['cs', 'ci', 'ch'],
                            help='The type of operation: cs, ci, ch, cN, sN')
        parser.add_argument('--timeout', default=300,
                            help="Specify a timeout for CSM in seconds. Default is 5 minutes (300)", type=int)
        parser.add_argument('--sn-max', type=int, default=8,
                            help='The maximal sn to try, relevant only for chirality')
        parser.add_argument('--normalizations', default=[],
                            help='Types of normalization available:\n'
                                 '0: standard normalization, according to centers of mass (without scaling)\n'
                                 '1: normalization according to the center of mass of each fragment\n'
                                 '2: normalization according to an approximation of the symmetric structure of the centers '
                                 'of mass of each fragment, based on the solution permutation\n'
                                 '3: normalization according to an approximation of the symmetric structure of the centers '
                                 'of mass of each fragment, without using the solution permutation\n'
                                 '4: normalization according to averages of approximation to symmetry of fragments\n'
                                 '5: normalization according to number of atoms\n'
                                 '6: linear normalization',
                            choices=['0', '1', '2', '3', '4', '5', '6'],
                            nargs='+', metavar="normalization"
                            )

    def add_input_output_utility_func(parser):
        parser_input_args = parser.add_argument_group("Args for input (requires --input. default is read from stdin)")
        parser_input_args.add_argument("--input", help="molecule file")
        parser_input_args.add_argument('--in-format', help='override guessing format from input file ending with provided format',
                                default=None)
        input_utility_func(parser_input_args)
        parser_output_args = parser.add_argument_group("Args for output (requires --output. default is json to stdout)")
        parser_output_args.add_argument("--output", help="output file")
        parser_output_args.add_argument('--out-format', help='override guessing format from output file ending with provided format',
                                default=None)
        output_utility_func(parser_output_args)


    parser = OurParser(allow_abbrev=False)
    commands = parser.add_subparsers(title="Available commands", dest="command")

    #READ
    input_args = commands.add_parser('read', help="Read a molecule file into a json in CSM format", usage="csm read filename [optional args]")
    input_args.add_argument('input', help='molecule file')
    input_args.add_argument('--format', help='override guessing format from file ending with provided format', default=None)
    input_utility_func(input_args)

    #WRITE
    out_args = commands.add_parser('write', help="Output the results of the calculation to a file", usage="csm write filename [optional args]")
    out_args.add_argument('output', default='output.txt', help='Output file')
    out_args.add_argument('--format', help='override guessing format from file ending with provided format',
                            default=None)
    output_utility_func(out_args)

    #EXACT
    exact_args_ = commands.add_parser('exact', help="Perform an exact CSM calculation", conflict_handler='resolve', usage='csm exact TYPE [optional args]')
    exact_args = exact_args_.add_argument_group("Args for exact calculation")
    shared_calc_utility_func(exact_args)
    exact_args.add_argument('--use-perm', type=str,
                            help='Compute exact CSM for a single permutation')
    exact_args.add_argument('--keep-structure', action='store_true', default=False,
                            help="Don't allow permutations that break bonds")
    exact_args.add_argument('--output-branches', action='store_true', default=False,
                            help="Don't allow permutations that break bonds")
    exact_args.add_argument('--output-perms', const="DEFAULT", nargs='?',
                            help='Writes all enumerated permutations to file. Default is current_directory/perms.csv, if --output is provided than the directory_from_that/perms.csv')
    add_input_output_utility_func(exact_args_)


    #APPROX
    approx_args_ = commands.add_parser('approx', help="Approximate the CSM value", conflict_handler='resolve', usage='csm approx TYPE [optional args]')
    approx_args = approx_args_.add_argument_group("Args for approx calculation")
    shared_calc_utility_func(approx_args)
    #choosing dir:
    approx_args.add_argument('--detect-outliers', action='store_true', default=False,
                             help="Use outlier detection to improve guesses for initial directions in approx algorithm")
    approx_args.add_argument('--no-orthogonal', action='store_true', default=False,
                             help="Don't add orthogonal directions to calculated directions")
    approx_args.add_argument('--fibonacci', type=int,
                             help="Use fibonacci sphere to generate N starting directions")
    approx_args.add_argument('--use-best-dir', action='store_true', default=False,
                             help='Only use the best direction')
    approx_args.add_argument('--dir', nargs=3, type=float,
                             help='run approximate algorithm using a specific starting direction')
    #algorithm choice
    approx_args.add_argument('--greedy', action='store_true', default=False,
                             help='use the old greedy approx algorithm (no hungarian)')
    approx_args.add_argument('--many-chains', action='store_true', default=False,
                             help='Use the new chains algorithm for many chains. Will automatically apply use-chains')
    approx_args.add_argument('--keep-structure', action='store_true', default=False,
                             help='Use keep-structure approximate algorithm')
    approx_args.add_argument('--selective', type=int,
                             help='Do a single iteration on many directions (use with --fibonacci), and then a full set of iterations only on the best k (default 10)')
    approx_args.add_argument('--parallel', type=int, const=0, nargs='?',
                             help='Calculate directions in parallel. Recommended for use with fibonacci. If no number of processors is specified, cpu count - 1 will be used')
    #outputs
    approx_args.add_argument('--statistics', const="DEFAULT", nargs='?',
                             help='Print statistics about each direction to a file. Default is current_directory/csm_statistics.txt, if --output is provided than the directory_from_that/csm_statistics.txt')
    approx_args.add_argument('--polar', action='store_true', default=False,
                             help="Print polar coordinates instead of cartesian coordinates in statistics")
    approx_args.add_argument('--print-approx', action='store_true', default=False,
                             help='print log to screen from approx')

    add_input_output_utility_func(approx_args_)


    #TRIVIAL
    trivial_args_ = commands.add_parser('trivial', help="Calculate trivial (identity) CSM", conflict_handler='resolve', usage='csm trivial TYPE [optional args]')
    trivial_args = trivial_args_.add_argument_group("Args for trivial calculation")
    shared_calc_utility_func(trivial_args)
    trivial_args.add_argument('--permute-chains', action='store_true', default=False)
    add_input_output_utility_func(trivial_args_)
    return parser

def _process_arguments(parse_res):
    def parse_input(dictionary_args):
        dictionary_args['in_file_name'] = parse_res.input
        dictionary_args['remove_hy'] = parse_res.remove_hy
        dictionary_args['ignore_symm'] = parse_res.ignore_sym
        dictionary_args['use_mass'] = parse_res.use_mass
        dictionary_args['babel_bond'] = parse_res.babel_bond
        dictionary_args['use_sequence'] = parse_res.use_sequence
        dictionary_args['use_chains'] = parse_res.use_chains
        dictionary_args['read_fragments'] = parse_res.read_fragments
        if not dictionary_args['use_chains'] and parse_res.read_fragments:
            dictionary_args['use_chains'] = True
            logger.warn(
                "--read-fragments is only relevant when --use-chains has been specified, so --use-chains has been specified automatically")

    def parse_output(dictionary_args):
        dictionary_args['out_file_name'] = parse_res.output
        dictionary_args['json_output'] = parse_res.json_output
        dictionary_args['print_local'] = dictionary_args['calc_local'] = parse_res.print_local
        dictionary_args['print_denorm'] = parse_res.print_denorm

    dictionary_args = {}
    dictionary_args["command"]=parse_res.command
    if parse_res.command == "read":
        dictionary_args["in_format"]=parse_res.format
        parse_input(dictionary_args)
    elif parse_res.command == "write":
        dictionary_args["out_format"] = parse_res.format
        parse_output(dictionary_args)
    else:
        # get input/output if relevant
        if parse_res.input != None:
            parse_input(dictionary_args)
            dictionary_args["in_format"] = parse_res.in_format
        else:
            dictionary_args["in_file_name"]=None
        if parse_res.output != None:
            parse_output(dictionary_args)
            dictionary_args["out_format"] = parse_res.out_format
        else:
            dictionary_args["out_file_name"]=None

        # get shared arguments:
        op = Operation(parse_res.type)
        dictionary_args['operation'] = op
        #dictionary_args['op_type'] = op.type
        #dictionary_args['op_order'] = op.order
        #dictionary_args['op_name'] = op.name

        dictionary_args['timeout'] = parse_res.timeout
        dictionary_args['sn_max'] = parse_res.sn_max
        dictionary_args['normalizations']=parse_res.normalizations

        if parse_res.command == 'exact':
            if parse_res.use_perm:
                dictionary_args['perm_file_name'] = parse_res.use_perm
            dictionary_args['keep_structure'] = parse_res.keep_structure
            #dictionary_args['no_constraint'] = parse_res.no_constraint
            dictionary_args['print_branches'] = parse_res.output_branches
            permuters.print_branches = parse_res.output_branches

            dictionary_args['perms_csv_name'] = parse_res.output_perms
            if parse_res.output_perms=="DEFAULT":
                try:
                    base_path= os.path.dirname(os.path.abspath(dictionary_args["out_file_name"]))
                    dictionary_args['perms_csv_name']=os.path.join(base_path, "perms.csv")
                except:
                    dictionary_args['perms_csv_name'] = os.path.join("perms.csv")




        if parse_res.command == 'approx':
            #choose dir:
            dictionary_args['detect_outliers'] = parse_res.detect_outliers
            dictionary_args['get_orthogonal'] = not parse_res.no_orthogonal
            if parse_res.fibonacci is not None:
                dictionary_args["fibonacci"] = True
                dictionary_args["num_dirs"] = parse_res.fibonacci
            dictionary_args['use_best_dir'] = parse_res.use_best_dir
            dir = parse_res.dir
            if dir:
                dictionary_args['dirs'] = [dir]

            #algorithm choice:
            dictionary_args['approx_algorithm'] = 'hungarian'
            if parse_res.greedy:
                dictionary_args['approx_algorithm'] = 'greedy'
            if parse_res.many_chains:
                if parse_res.greedy:
                    raise ValueError("--many-chains and --greedy are mutually exclusive")
                dictionary_args['use_chains'] = True
                dictionary_args['approx_algorithm'] = 'many-chains'
            if parse_res.keep_structure:
                dictionary_args['approx_algorithm'] = 'structured'

            if parse_res.selective is not None:
                dictionary_args["selective"] = True
                dictionary_args["num_selected"] = parse_res.selective

            dictionary_args['parallel'] = parse_res.parallel is not None
            dictionary_args['pool_size'] = parse_res.parallel

            #outputs:
            dictionary_args['print_approx'] = parse_res.print_approx
            dictionary_args['polar'] = parse_res.polar
            dictionary_args['stat_file_name'] = parse_res.statistics
            if parse_res.statistics=="DEFAULT":
                if dictionary_args["out_file_name"] is not None:
                    base_path= os.path.dirname(os.path.abspath(dictionary_args["out_file_name"]))
                    dictionary_args['stat_file_name']=os.path.join(base_path, "csm_statistics.txt")
                else:
                    dictionary_args['stat_file_name'] = os.path.join("csm_statistics.txt")


    return dictionary_args

def get_parsed_args(args):
    parser = _create_parser()
    parsed_args = parser.parse_args(args)
    if parsed_args.command is None:
        parser.error("You must select a command from: read, exact, approx, trivial, write")
    processed_args = _process_arguments(parsed_args)
    return processed_args
