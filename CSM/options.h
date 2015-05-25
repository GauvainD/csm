/*
 * The CSM runtime options
 *
 * Extracted from mainRot.cpp during the 2014 reorganization
 * Created by Itay Zandbank
 */

#ifndef OPTIONS_H
#define OPTIONS_H

#include <string>
#include <vector>

typedef enum {
	CN,
	SN,
	CS,
	CI,
	CH
} OperationType;

class Molecule;  // Forward reference

struct csm_options
{
	std::string opName;
	bool printNorm;
	bool printLocal;
	bool writeOpenu;
	std::string format;

	bool ignoreHy;
	bool removeHy;
	bool ignoreSym;
	bool useFormat;
	OperationType type;
	int opOrder;
	bool useperm;
	bool useDir;
	bool findPerm;
	bool useMass;
	bool limitRun;
	bool babelBond;
	bool timeOnly;
	int sn_max;
	bool detectOutliers;
	bool babelTest;
	bool keepCenter;
	std::string logFileName;

	// file pointers
	FILE* outFile;
	std::string inFileName;
	std::string outFileName;

	std::vector<double> dir;
	std::vector<int> perm;

	Molecule *molecule;  // The molecule to be used

	csm_options();
};

extern csm_options options;

#endif