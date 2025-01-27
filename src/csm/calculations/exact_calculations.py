import sys

import numpy as np
from csm.fast import CythonPermuter, SinglePermPermuter
from csm.fast import calc_ref_plane, calc_ref_plane_prochirality

from csm.calculations.basic_calculations import check_perm_cycles, now, run_time
from csm.calculations.constants import MIN_DOUBLE, MAX_DOUBLE
from csm.calculations.data_classes import CSMState, CSMResult, Operation, BaseCalculation
from csm.calculations.permuters import ConstraintPermuter
from csm.input_output.formatters import csm_log as print
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


class ExactStatistics:
    def __init__(self, permuter):
        self._perm_count = permuter.count
        self._truecount = permuter.truecount
        self._falsecount = permuter.falsecount

    def write(self, f=sys.stderr):
        f.write("Number of permutations: %s" % format_perm_count(self.perm_count))
        f.write("Number of branches in permutation tree: %s" % format_perm_count(self.num_branches))
        f.write("Number of dead ends: %s" % format_perm_count(self.dead_ends))

    def to_dict(self):
        return {
            "perm count": self.perm_count,
            "number branches": self.num_branches,
            "dead ends": self.dead_ends
        }

    @property
    def dead_ends(self):
        return self._falsecount

    @property
    def perm_count(self):
        return self._perm_count

    @property
    def num_branches(self):
        return self._truecount


class ExactCalculation(BaseCalculation):
    def __init__(self, operation, molecule, keep_structure=False, perm=None,
                 no_constraint=False, callback_func=None, prochirality=False,
                 *args, **kwargs):
        """
        A class for running the exact CSM Algorithm
        :param operation: instance of Operation class or named tuple, with fields for name and order, that describes the symmetry
        :param molecule: instance of Molecule class on which the described symmetry calculation will be performed
        :param keep_structure: boolean, when True only permutations that maintain bond integrity will be measured 
        :param perm: a list of atom indiced describing one permutation of the molecule. Default None- When provided,
         only the provided permutation is measured
        :param no_constraint: boolean, default False, when False the constraints algorithm is used for the permuter, 
        when True the old permuter is used
        :param timeout: default 300, the number of seconds the function will run before timing out
        :param callback_func: default None, this function is called for every single permutation calculated with an argument of a single 
        CSMState, can be used for printing in-progress reports, outputting to an excel, etc.
        :param prochirality: Indicates whether we want a measure of chirality
        or prochirality.
        """
        super().__init__(operation, molecule)
        self.keep_structure = keep_structure
        self.perm = perm
        self.no_constraint = no_constraint
        self.callback_func = callback_func
        self.prochirality = prochirality

    def calculate(self, timeout=300, *args, **kwargs):
        best_result=super().calculate(timeout)
        overall_stats = self.statistics.to_dict()
        overall_stats["runtime"] = run_time(self.start_time)
        self._csm_result = CSMResult(best_result, self.operation, overall_stats=overall_stats)
        return self.result

    def _create_permuter(self, op, timeout):
        op_type=op.type
        op_order=op.order
        molecule=self.molecule
        keep_structure=self.keep_structure
        perm=self.perm
        no_constraint=self.no_constraint
        if perm:
            perm_arr = np.array(perm, dtype="long")
            if (perm_arr >= 0).all():
                permuter = SinglePermPermuter(perm_arr, molecule, op_order, op_type)
            else:
                raise ValueError("The permutation in the function '_calculate' contains negative numbers: \n{}".format(perm_arr))
        else:
            permuter = ConstraintPermuter(molecule, op_order, op_type, keep_structure, timeout=timeout)
            if no_constraint:
                permuter = CythonPermuter(molecule, op_order, op_type, keep_structure, timeout=timeout)
        return permuter

    def _calculate_internal(self, op, timeout, permuter, fixed_vectors):
        op_type=op.type
        op_order=op.order
        molecule=self.molecule
        keep_structure=self.keep_structure
        perm=self.perm
        no_constraint=self.no_constraint
        prochirality=self.prochirality

        best_csm = CSMState(molecule=molecule, op_type=op_type, op_order=op_order, csm=MAX_DOUBLE)
        traced_state = CSMState(molecule=molecule, op_type=op_type, op_order=op_order)
        permuter.permute()
        for calc_state in permuter.permute():

            #print(calc_state.perm)
            if permuter.count % 1000000 == 0:
                print("calculated for", int(permuter.count / 1000000), "million permutations thus far...\t Time:",
                      run_time(self.start_time))
            if not prochirality or fixed_vectors is None:
                csm, dir, v1, v2 = calc_ref_plane(op_order, op_type == 'CS',
                                                  calc_state, prochirality and
                                                  fixed_vectors is None)
            else:
                csm, dir, v1, v2 = calc_ref_plane_prochirality(op_order, calc_state, fixed_vectors[0],
                                            fixed_vectors[1])


            #print(csm, dir, v1, v2)
            if self.callback_func:
                traced_state = traced_state._replace(csm=csm, perm=calc_state.perm, dir=dir)
                traced_state.serial = permuter.count
                self.callback_func(traced_state)

            if csm < best_csm.csm:
                best_csm = best_csm._replace(csm=csm, dir=dir, perm=list(calc_state.perm))
                if abs(csm) < 1e-9:
                    return best_csm, True, v1, v2
        return best_csm, False, None, None

    def _calculate(self, op, timeout):
        """
        Calculates minimal csm, directional cosines by applying permutations that keep the similar atoms within the group.
        :param operation: cannot be CH.
        :param molecule:
        :param keep_structure:
        :param perm:
        :param no_constraint:
        :param suppress_print:
        :param timeout:
        :return:
        """
        op_type=op.type
        op_order=op.order
        molecule=self.molecule
        keep_structure=self.keep_structure
        perm=self.perm
        no_constraint=self.no_constraint
        prochirality=self.prochirality

        permuter = self._create_permuter(op, timeout)

        fixed_vectors = None
        best_csm, zero_chirality, v1, v2 = self._calculate_internal(op, timeout,
                                                                    permuter,
                                                                    fixed_vectors)

        print(prochirality, zero_chirality)
        if prochirality and zero_chirality:
            print(f"Found symmetry {best_csm.dir}. Computing prochirality.")
            permuter = self._create_permuter(op, timeout)
            fixed_vectors=[v1, v2]
            best_csm, _, v1, v2 = self._calculate_internal(op, timeout,
                                                                        permuter,
                                                                        fixed_vectors)

        self.statistics = ExactStatistics(permuter)

        if best_csm.csm == MAX_DOUBLE:
            # failed to find csm value for any permutation
            # best_csm = best_csm._replace(csm=csm, dir=dir, perm=list(calc_state.perm))
            raise CSMValueError("Failed to calculate a csm value for %s %d" % (op_type, op_order), best_csm)
        best_csm = best_csm._replace(is_chiral = not zero_chirality)
        return best_csm

    @staticmethod
    def exact_calculation_for_approx(operation, molecule, perm, prochirality=False):
        ec = ExactCalculation(operation, molecule, perm=perm, prochirality=prochirality)
        if operation.type == 'CH':  # Chirality
            raise ValueError("How did you get here? Approx should be sending chirality broken down to cs, Sns")

        best_result = ec._calculate(operation, molecule)
        falsecount, num_invalid, cycle_counts, bad_indices = check_perm_cycles(perm, operation)
        best_result = best_result._replace(num_invalid=num_invalid)
        return best_result

    @property
    def result(self):
        return self._csm_result
