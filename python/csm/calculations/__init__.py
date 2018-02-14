"""
This module is for all the calculations that power the CSM calculation
"""
from csm.calculations.approx.approximators import ApproxCalculation
from csm.calculations.exact_calculations import ExactCalculation
from csm.calculations.trivial_calculations import TrivialCalculation
from csm.calculations.approx.dirs import DirectionChooser

#approx=approx_calculation
#exact=exact_calculation
#trivial=trivial_calculation
Approx=ApproxCalculation
Exact=ExactCalculation
Trivial=TrivialCalculation