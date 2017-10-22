import datetime
import itertools

import math

import numpy as np
from csm.calculations.basic_calculations import process_results, CSMState
from csm.calculations.constants import MINDOUBLE, MAXDOUBLE, start_time
from csm.fast import calc_ref_plane

from csm.fast import CythonPermuter, SinglePermPermuter
from csm.calculations.permuters import ConstraintPermuter
import logging

from csm.input_output.formatters import format_perm_count

np.set_printoptions(precision=6)


__author__ = 'Itay, Devora, Yael'



# When this property is set by an outside caller, it is called every permutation iteration with the current CSMState
# This is useful for writing all permutations to file during the calculation
csm_state_tracer_func = None

class CSMValueError(ValueError):
    def __init__(self, arg1, CSMState):
        self.arg1 = arg1
        self.CSMState = CSMState
        super().__init__(arg1)


class Calculation:
    def __init__(self, operation, molecule):
        self.operation=operation
        self.molecule=molecule

    def calc(self):
        pass

    @property
    def result(self):
        return self._csm_result


class ExactCalculation(Calculation):
    def __init__(self, operation, molecule, sn_max=8, keep_structure=False, perm=None, no_constraint=False, timeout=300, callback_func=None, *args, **kwargs):
        super().__init__(operation, molecule)
        self.sn_max=sn_max
        self.keep_structure=keep_structure
        self.perm=perm
        self.no_constraint=no_constraint
        self.timeout=timeout
        self.callback_func=callback_func
        self.calc()

    def calc(self):
        op_type=self.operation.type
        op_order=self.operation.order
        molecule=self.molecule
        keep_structure=self.keep_structure
        perm=self.perm
        no_constraint=self.no_constraint
        sn_max=self.sn_max
        timeout=self.timeout

        if op_type == 'CH':  # Chirality
            # sn_max = op_order
            # First CS
            best_result = self.csm_operation('CS', 2, molecule, keep_structure, perm, no_constraint, timeout)
            best_result = best_result._replace(op_type='CS')  # unclear why this line isn't redundant
            if best_result.csm > MINDOUBLE:
                # Try the SN's
                for op_order in range(2, sn_max + 1, 2):
                    result = self.csm_operation('SN', op_order, molecule, keep_structure, perm, no_constraint, timeout)
                    if result.csm < best_result.csm:
                        best_result = result._replace(op_type='SN', op_order=op_order)
                    if best_result.csm < MINDOUBLE:
                        break

        else:
            best_result = self.csm_operation(op_type, op_order, molecule, keep_structure, perm, no_constraint, timeout)

        self._csm_result = process_results(best_result)
        return self.result

    def csm_operation(self, op_type, op_order, molecule, keep_structure=False, perm=None, no_constraint=False, timeout=300):
        """
        Calculates minimal csm, directional cosines by applying permutations that keep the similar atoms within the group.
        :param op_type: cannot be CH.
        :param op_order:
        :param molecule:
        :param keep_structure:
        :param perm:
        :param no_constraint:
        :param suppress_print:
        :param timeout:
        :return:
        """
        best_csm = CSMState(molecule=molecule, op_type=op_type, op_order=op_order, csm=MAXDOUBLE)
        traced_state = CSMState(molecule=molecule, op_type=op_type, op_order=op_order)

        if perm:
            permuter = SinglePermPermuter(np.array(perm), molecule, op_order, op_type)
        else:
            permuter = ConstraintPermuter(molecule, op_order, op_type, keep_structure, timeout=timeout)
            if no_constraint:
                permuter = CythonPermuter(molecule, op_order, op_type, keep_structure, timeout=timeout)

        for calc_state in permuter.permute():
            if permuter.count % 1000000 == 0:
                print("calculated for", int(permuter.count / 1000000), "million permutations thus far...\t Time:",
                      datetime.datetime.now() - start_time)
            csm, dir = calc_ref_plane(op_order, op_type == 'CS', calc_state)

            if self.callback_func:
                traced_state = traced_state._replace(csm=csm, perm=calc_state.perm, dir=dir)
                self.callback_func(traced_state)

            if csm < best_csm.csm:
                best_csm = best_csm._replace(csm=csm, dir=dir, perm=list(calc_state.perm))

        self._perm_count=permuter.count
        self._truecount=permuter.truecount
        self._falsecount=permuter.falsecount

        if best_csm.csm == MAXDOUBLE:
            # failed to find csm value for any permutation
            best_csm = best_csm._replace(csm=csm, dir=dir, perm=list(calc_state.perm))
            raise CSMValueError("Failed to calculate a csm value for %s %d" % (op_type, op_order), best_csm)
        return best_csm

    @property
    def dead_ends(self):
        return self._falsecount

    @property
    def perm_count(self):
        return self._perm_count

    @property
    def num_branches(self):
        return self._truecount


class PlaceHolderOperation:
    def __init__(self, op_type, op_order):
        self.type = op_type
        self.order = op_order

def exact_calculation(op_type, op_order, molecule, sn_max=8, keep_structure=False, perm=None, no_constraint=False, suppress_print=False, timeout=300, *args, **kwargs):
    ec= ExactCalculation(PlaceHolderOperation(op_type, op_order), molecule, sn_max, keep_structure, perm, no_constraint, timeout)
    if not perm and not suppress_print:
        print("Number of permutations: %s" % format_perm_count(ec.perm_count))
        print("Number of branches in permutation tree: %s" % format_perm_count(ec.num_branches))
        print("Number of dead ends: %s" % format_perm_count(ec.dead_ends))
    return ec.result










