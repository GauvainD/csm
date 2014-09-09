/*
 * Author: shadi lahham
 *
 * generates permutations in the range 1 .. size
 * the permutations are generated by a group of permuters that
 * are "chained in a series" such that the effect is cumulative.
 *
 */

#ifndef GROUP_PERMUTER_H
#define GROUP_PERMUTER_H

#include "permuter.h"

class GroupPermuter
{
private:
	int _numberOfGroups;
	int* _sizesOfGroups;
	int _size;
	int* _index;
	Permuter** _permuters;
	bool _firstPermutation;  // boolean flag - the first permuation is unique, not permuted

	void copyIndexes();
public:
	/**
	* Create a group permuter for a single molecule,
	* containing a permutation enumerator for each equivalence group
	*
	* @param numberOfGroups The number of equivalence groups in the molecule
	* @param sizesOfGroups The size of each group
	* @param totalSize The number of atoms in the molecule
	* @param permutationGroupSize The size of allowed cycles (in addition to cycles of size 1)
	* @param addGroupsOfTwo Should cycles of size 2 also be allowed
	*
	* @return The new groupPermuter
	*/
	GroupPermuter(int numberOfGroups, int* sizeOfGroups, int totalSize, int permutationGroupSize, int addGroupsOfTwo);
	~GroupPermuter();

	/**
	* Generate the next permutation
	*
	* @return true if we have not yet reached the end of the enumerator, false otherwise
	*/
	bool next();

	/**
	* Reset the group permuter to re-initialize enumeration
	*/
	void reset();

	/*
	* Returns one permuation element
	*
	* @param index The element index in the permutation
	* @returns an element at index @index
	*/
	const int elementAt(int index) const
	{
		return (*this)[index];
	}

	const int operator[](int index) const;
};


#endif
