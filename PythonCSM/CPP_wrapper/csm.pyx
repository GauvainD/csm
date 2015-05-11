""" The Python wrapper of csmlib """

import sys
cimport csmlib

def SayHello():
    return csmlib.SayHello()

def cs(s):
    """ Converts a Python string to a C++ string """
    return s.encode('UTF8')

def RunCSM(args):
    cdef csmlib.python_cpp_bridge options

    options.opType = cs(args['type'])
    options.opName = cs(args['opName'])
    options.opOrder = args['opOrder']

    options.printNorm = args['printNorm']
    options.printLocal = args['printLocal']
    options.writeOpenu = args['writeOpenu']

    if args['format']:
        options.format = cs(args['format'])

    options.ignoreHy = args['ignoreHy']
    options.removeHy = args['removeHy']
    options.ignoreSym = args['ignoreSym']

    options.findPerm = args['findPerm']
    options.useMass = args['useMass']
    options.limitRun = args['limitRun']
    options.babelBond = args['babelBond']
    options.timeOnly = args['timeOnly']
    if args['sn_max']:
        options.sn_max = args['sn_max']

    options.detectOutliers = args['detectOutliers']
    options.babelTest = args['babelTest']
    options.keepCenter = args['keepCenter']

    if 'logFile' in args:
        options.logFilename = cs(args['logFile'])

    options.inFilename = cs(args['inFileName'])
    options.fdIn = args['inFile'].fileno()

    options.outFilename = cs(args['outFileName'])
    options.fdOut = args['outFile'].fileno()

    if 'permFile' in args:
        options.fdPerm = args['permFile'].fileno()
    if 'dirFile' in args:
        options.fdDir = args['dirFile'].fileno()

    print("Calling C++ from Python")
    result = csmlib.RunCSM(options)
    print("Returning to Python")
    return result
