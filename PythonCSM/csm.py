"""
The main entry point of the Python CSM
"""
import math
import sys

from arguments import get_arguments
from calculations.normalizations import normalize_coords, de_normalize_coords

__author__ = 'zmbq'

from input_output.writers import print_all_output
from calculations.csm_calculations_data import CSMCalculationsData
from calculations.csm_calculations import perform_operation, MAXDOUBLE, total_number_of_permutations
# from CPP_wrapper import csm

import logging

MINDOUBLE = 1e-8
APPROX_RUN_PER_SEC = 8e4


sys.setrecursionlimit(10000)

def process_results(results, csm_args):
    """
    Final normalizations and de-normalizations
    :param results: CSM calculations results
    :param csm_args: CSM args
    """
    results.molecule.set_norm_factor(csm_args['molecule'].norm_factor)
    masses = [atom.mass for atom in results.molecule.atoms]


    normalize_coords(results.outAtoms, masses, csm_args['keepCenter'])

    results.molecule.de_normalize()
    results.outAtoms = de_normalize_coords(results.outAtoms, results.molecule.norm_factor)

logger = None

def init_logging(csm_args):
    global logger

    if 'logFileName' in csm_args:
        logging.basicConfig(filename=csm_args['logFileName'], level=logging.DEBUG,
                            format='[%(asctime)-15s] [%(levelname)s] [%(name)s]: %(message)s')
    else:
        logging.basicConfig(level=logging.ERROR)
    logger = logging.getLogger("csm")


def run_csm(args, print_output=True):
    try:
        csm_args = get_arguments(args)
        init_logging(csm_args)
        csm_args['molecule'].preprocess(**csm_args)
        # csm.SetCSMOptions(csm_args)  # Set the default options for the Python/C++ bridge

        if csm_args['babelTest']:
            return None

        if not csm_args['findPerm']:
            if 'perm' not in csm_args and 'dir' not in csm_args:
                total_perms = total_number_of_permutations(csm_args)
                time = 1.0 * total_perms / 3600 / APPROX_RUN_PER_SEC
                if math.isnan(time):
                    # time is NaN
                    time = MAXDOUBLE
                print("Going to enumerate over %d permutations" % total_perms)
                print("Entire run should take approx. %.2lf hours on a 2.0Ghz Computer" % time)
            else:
                print("Using 1 permutation")
                print("Run should be instantaneous")

            if csm_args['timeOnly']:
                return None

        data = CSMCalculationsData(csm_args)

        # Code from the old mainRot.cpp
        if 'perm' in csm_args:
            result = csm.RunSinglePerm(data)
        else:
            if csm_args['type'] != 'CH':
                result = perform_operation(csm_args, data)
            else:
                # chirality support
                data.operationType = data.chMinType = "CS"
                data.opOrder = 2
                result = perform_operation(csm_args, data)

                if result.csm > MINDOUBLE:
                    data.operationType = "SN"
                    for i in range(2, csm_args['sn_max'] + 1, 2):
                        data.opOrder = i
                        ch_result = perform_operation(csm_args, data)
                        if ch_result.csm < result.csm:
                            result = ch_result
                            result.chMinType = 'SN'
                            result.chMinOrder = ch_result.opOrder

                        if result.csm < MINDOUBLE:
                            break

        if csm_args['printLocal']:
            if csm_args['type'] == 'CH':
                data.opOrder = result.chMinOrder
            local_res = csm.ComputeLocalCSM(data)
            result.localCSM = local_res.localCSM

        process_results(result, csm_args)

        if print_output:
            print_all_output(result, csm_args)

        return result
    finally:
        try:
            csm_args['outFile'].close()
            csm_args['outPermFile'].close()
        except:
            pass


if __name__ == '__main__':
    results = run_csm(sys.argv[1:])
