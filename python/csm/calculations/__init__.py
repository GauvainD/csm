"""
This module is for all the calculations that power the CSM calculation
"""
from csm.calculations.approx.main import approx_calculation, ApproxCalculation
from csm.calculations.exact_calculations import exact_calculation, ExactCalculation
from csm.calculations.trivial_calculations import trivial_calculation, TrivialCalculation

approx=approx_calculation
exact=exact_calculation
trivial=trivial_calculation
Approx=ApproxCalculation
Exact=ExactCalculation
Trivial=TrivialCalculation