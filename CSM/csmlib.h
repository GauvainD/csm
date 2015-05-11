/*
 * The interface of the CSM library.
 * The CSM library is going to be called from Python using Cython. The library's outside interface is going
 * to be located in this file, and call internal functions as necessary.
 *
 * This file is going to change continiously, until we end up with the core C++ calculations and a big Python codebase.
 *
 * By Itay Zandbank
 */

#ifndef CSMLIB_H
#define CSMLIB_H

#include <vector>
#include <string>
#include "options.h"

// Cython works much better with a C interface, use it

struct python_cpp_bridge
{
	std::string opType;
	std::string opName;
	int opOrder;

	bool printNorm;
	bool printLocal;
	bool writeOpenu;
	std::string format;

	bool ignoreHy;
	bool removeHy;
	bool ignoreSym;
	bool findPerm;
	bool useMass;
	bool limitRun;
	bool babelBond;
	bool timeOnly;
	int sn_max;
	bool detectOutliers;
	bool babelTest;
	bool keepCenter;
	std::string logFilename;
	std::string inFilename;
	std::string outFilename;

	// File descriptors - -1 means no file
	int fdIn, fdOut;

	// Direction Axis
	std::vector<double> dir;

	//Permutation
	std::vector<int> perm;

	python_cpp_bridge();
};


#ifdef __cplusplus
extern "C"
{
#endif
	// Runs the entire CSM application
	// int RunCSM(const std::vector<std::string> args);
	int RunCSM(python_cpp_bridge options);
	int SayHello();
#ifdef __cplusplus
}
#endif
#endif