This fork adds the functionality to measure the prochirality of a molecule.

Special thanks to Christophe Troestler for his precious help.

# Usage

```
csm (exact | trivial) cs [--remove-hy] --prochirality [--simple] [--timeout TIME_IN_S] --input FILE
```

**Use one of exact or trivial.**

The arguments are (arguments between [] are optional):

* exact or trivial: enter exact to compute the prochirality over all permutations and trivial to only use the identity permutation
* cs: the original implementation supports multiple operations. Here we only use cs which is the symmetry plane operation.
* --remove-hy: This option runs the computation without the hydrogen atoms. This reduces the number of permutations.
* --prochirality: We want to measure prochirality.
* --simple: to only output data to the terminal and not write result files.
* --timeout TIME\_IN\_S: By default, the computation stops after 300s. If this is too short, it can be changed by giving a different number of seconds.
* --input FILE: the name of the file containing the molecule.

# Installation (tested in Debian and Arch Linux)

## Dependencies
In order to use this version, the following dependencies must be installed:
- Openbabel (including its dev library): used by the software to load molecules.
- swig: used by pip to compile csm\_openbabel, the python bindings to openbabel

## Compiling

From the src directory, run the following commands:

```
python setup.py prepare
python setup.py build_ext
python setup.py install
```

This should compile the C++ code and install the `csm` command using python.

This can be done in a venv environment using the python venv utility:

```
python -m venv ENVNAME
source ENVNAME/bin/activate
```

Then run the commands above.

## Using docker

In order to simplify installation, a Dockerfile has been written. It can be used with the following commands:

## Building the image

To build the docker image (from the csm directory, not src):

```
docker build --tag IMAGENAME -f Dockerfile.prochirality .
```

This should build a docker image named IMAGENAME which can then be used. Replace IMAGENAME by a name of your choice.

## Running the image

In order to run the image, use the following command (it should work from any directory):

```
docker run [--rm] -it -v DIRECTORY:/home/prochirality IMAGENAME bash
```

It should open a terminal where one can run the commands explained in `Usage`. This terminal can be closed using either Ctrl+D or the command exit.

The arguments are as follows (again arguments between [] are optional):

* --rm: deletes the container when the image is stopped.
* -it: Is used to have an interactive terminal. Without it, we cannot run commands.
* -v DIRECTORY:/home/prochirality: This option makes it so that the container has access to the DIRECTORY where the molecules files are stored. Replace DIRECTORY with the one where you have the .pdb files, for example.
* IMAGENAME: the name you chose when creating the container.

# CSM

# About

The CSM program calculates continuous symmetry and chirality measures of molecules with respect to a given point group G. Molecular coordinates can be provided in either xyz, sdf, mol or pdb format.
An online calculator is available at: https://csm.ouproj.org.il. 


## Features

* The codes cover the following point groups: C<sub>s</sub>, C<sub>i</sub>, C<sub>n</sub> (n>=2), S<sub>n</sub> (n= 2,4,6,…).
* Input structures can be in the form of a single molecule, concatenated file with multiple structures and a directory of molecules.
* When connectivity data is missing, OpenBabel is used to deduce it.

### Available commands
* comfile - Provide a command file for running calculations
* read - Read a molecule file into a json in CSM format
* write - Output the results of the calculation to a file. Must be used with piped input
* exact - Perform an exact CSM calculation for small-to-medium size molecules in xyz, mols, sdf and pdb file format. 
* approx - Approximate the CSM value. Relevant for protein homomers  in pdb file format. Partially tested for large molecules as well.
* trivial - Use the unit permutation to calculate the CSM for molecules and protein homomers.

## Citations

Please cite the CSM using the following:

### Exact algorithm:

* Alon G. and Tuvi-Arad I., "Improved algorithms for symmetry analysis: Structure preserving permutations", J. Math. Chem., 56(1), 193-212 (2018).

### Approx algorithm:

* Tuvi-Arad I. and Alon G., "Improved Algorithms for Quantifying the Near Symmetry of Proteins: Complete Side Chains Analysis", Journal of Cheminformatics, 11(1): 39 (2019).

* Dryzun C., Zait A. and Avnir D., "Quantitative Symmetry and Chirality - A Fast Computational Algorithm for Large Structures: Proteins, Macromolecules, Nanotubes, and Unit Cells", J. Comput. Chem., 32, 2526-2538 (2011).

### Original Code by Avnir and coworkers:

* Pinsky M., Dryzun C., Casanova D., Alemany P., Avnir D., "Analytical Methods for Calculating Continuous Symmetry Measures and the Chirality Measure", Journal of Computational Chemistry 29(16): 2712-2721 (2008).

* Zabrodsky, H.; Avnir, D. Continuous symmetry measures .4. Chirality. J. Am. Chem. Soc. 117: 462-473 (1995).

* Zabrodsky H., Peleg S., Avnir D., "Continuous symmetry measures", Journal of the American Chemical Society 114(20): 7843-7851 (1992).



## Usage

Input data requires a molecular geometry file and a choice of a point group
After installation, the program can be called from the command line. For example, to calculate the measure with respect to the C<sub>2</sub> point group one should type:

```bash
csm  exact c2 --input input_mol.sdf --output output_dir --keep-structure
```

For a list of all available options type `csm --help`

In addition to the possibility of using CSM from the command line, CSM can be accessed programmatically through its API. Details are in the file API.md (including examples).

## Installation

CSM can be installed on Windows and Linux machines.

The easiest way to install the CSM is through [Docker](https://hub.docker.com/r/teamcsm/csm/tags).

### Build Instructions: Windows

Install [OpenBabel 3.1.1](https://github.com/openbabel/openbabel/releases/tag/openbabel-3-1-1)  
Test open babel with the command: `obabel -H` , if it doesn't work, try to restart your computer.  

From within the python folder, run:
`pip install -r requirements.txt`  

Run the build cython commands:  
`python\csm\CPP_wrapper> python .\setup.py build`  
`python\cython-munkres> .\rebuild.bat`  



### Build Instructions: Linux

Because installing openbabel correctly is a delicate and bug-prone process, an alternative method of installing CSM is available using [PyPI](https://pypi.org/project/csm/). Please note that this is an older version of the software. 

The newest version is available through [Docker](https://hub.docker.com/r/teamcsm/csm/tags).

## Credits

**Science/Math:**

* Prof. Inbal Tuvi-Arad, Department of Natural Sciences, The Open University of Israel

* Dr. Gil Alon, Department of Mathematics and Computer Science, The Open University of Israel

* Prof. David Avnir, Institute of Chemistry, The Hebrew University of Jerusalem

**Programming:**

* The Research Software Company

**Testing, scripts, and additional technical support:**

* Sagiv Barhoom, The Open University of Israel

**Intensive testing:**

* Yaffa Shalit, Department of Natural Sciences, The Open University of Israel

* The code for the Hungarian algorithm is copyright (c) 2012, Jacob Frelinger


## Contact ##

For questions about the code, feature requests, and bug reports, feel free to use [the CoSyM website users group](https://groups.google.com/g/csm-openu). 

## License ##
This project is provided under the GPL 2 license. See `LICENSE.txt` for more information.
