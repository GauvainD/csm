from openbabel import OBAtom, OBElementTable, OBAtomAtomIter, OBConversion, OBMol
from molecule.atom import Atom
from molecule.normalizations import normalize_coords, de_normalize_coords
from molecule.readers import read_file
import logging
logger = logging.getLogger("csm")

class Molecule:
    def __init__(self, atoms={}, chains={}, norm_factor=1.0):
        self._atoms=atoms
        self._chains=chains
        self._bondset=set()
        self._equivalence_classes=[]
        self._norm_factor= norm_factor
        self._flags={}
        self._create_bondset()
    @property
    def atoms(self):
        return self._atoms

    @property
    def bondset(self):
        return self._bondset

    @property
    def equivalence_classes(self):
        return self._equivalence_classes

    @property
    def norm_factor(self):
        # Normalization factor. Defaults to 1.0 if normalize wasn't called
        return self._norm_factor

    @property
    def chains(self):
        return self._chains
    def has_bond(self, atom_i, atom_j):
        if (atom_i, atom_j) in self._bondset:
            return True
        return False

    def _create_bondset(self):
        for i in range(len(self._atoms)):
            for match in self._atoms[i].adjacent:
               self._bondset.add((i, match))

    def _find_equivalence_classes(self):
        group_num = 0
        groups = []
        atoms_size = len(self._atoms)
        marked = set()

        atoms_group_num = {}

        logger.debug("Breaking molecule into similarity groups")

        # break into initial groups by symbol and valency
        for i in range(atoms_size):
            if i in marked:
                continue

            groups.append([])

            for j in range(atoms_size):
                if j in marked \
                        or len(self._atoms[i].adjacent) != len(self._atoms[j].adjacent) \
                        or self._atoms[i].symbol != self._atoms[j].symbol:
                    continue

                groups[group_num].append(j)
                atoms_group_num[j] = group_num
                marked.add(j)

            group_num += 1

        # iteratively refine the breakdown into groups
        # break into subgroups at an infinite depth - as long as there's something to break, it is broken

        divided_group = True
        num_iters = 0

        while divided_group:
            num_iters += 1
            divided_group = False

            new_groups = []

            for i, group in enumerate(groups):
                first_elem = group[0]
                group_size = len(group)

                sub_group = []

                # for each item in the group (except the first) check if it can be split or not
                for j in range(1, group_size):
                    if not self.is_similar(atoms_group_num, group[j], first_elem):
                        # add elem to new subGroup
                        sub_group.append(group[j])
                        group[j] = -1

                if len(sub_group) > 0:
                    divided_group = True
                    new_groups.append(sub_group)
                    for el in sub_group:
                        atoms_group_num[el] = group_num
                    group_num += 1
                    # remove elements of sub_group from group
                    groups[i] = [el for el in group if el != -1]

            groups.extend(new_groups)

        logger.debug("Broken into groups with %d iterations." % num_iters)

        self._equivalence_classes = groups
        for group in groups:
            for atom_index in group:
                for equiv_index in group:
                    self._atoms[atom_index].add_equivalency(equiv_index)


        if self.chains:
            self.process_chains()

    def process_chains(self):
        # Divide all the equivalence classes so that no equivalence class includes two atoms from different chains
        divided_groups = []
        for group in self.equivalence_classes:
            sub_groups = {}
            for chain in self.chains:
                sub_groups[chain] = []
            for elem in group:
                sub_groups[self.atoms[elem].chain].append(elem)  # put an atom into a suitable chain sub_group
            for chain in sub_groups:
                if len(sub_groups[chain]) == len(group)/len(self._chains):  # check that all chains are the same length
                    divided_groups.append(sub_groups[chain])
                else:
                    raise ValueError("Illegal chains molecule structure")

        self._equivalence_classes = divided_groups

    def is_similar(self, atoms_group_num, a, b):
        found = True
        mark = set()

        valency_a = len(self._atoms[a].adjacent)
        valency_b = len(self._atoms[b].adjacent)

        # for each of i's neighbours
        for i in range(valency_a):
            found = False

            for j in range(valency_b):
                if j in mark:
                    continue

                if atoms_group_num[self._atoms[a].adjacent[i]] == atoms_group_num[self._atoms[b].adjacent[j]]:
                    # the i-th neighbour of 'a' belongs to the same group as the j-th neighbour of 'b'
                    found = True
                    mark.add(j)
                    break

            if not found:
                break

        return found

    def process_equivalency(self, remove_hy=False, ignore_hy=False):
        """
        Preprocess a molecule based on the arguments passed to CSM
        :param remove_hy: True if hydrogen atoms should be removed
        :param ignore_hy: True when hydrogen atoms should be ignored when calculating the equivalence classes
        :param keepCenter: True when the molecule's CoM shouldn't be moved
        :param kwargs: Place holder for all other csm_args.
        You can call it by passing **csm_args
        """
        if not remove_hy:
            self._find_equivalence_classes()

        if ignore_hy or remove_hy:
            if self._obmol:
                self._obmol.DeleteHydrogens()
            remove_list = ["H", " H"]
            self.strip_atoms(remove_list, ignore_hy)

    def normalize(self, keep_center=False):
        """
        Normalize the molecule
        :param keep_center:
        """
        coords = [atom.pos for atom in self._atoms]
        masses = [atom.mass for atom in self._atoms]
        (norm_coords, self._norm_factor) = normalize_coords(coords, masses, keep_center)
        size = len(self._atoms)
        for i in range(size):
            self._atoms[i].pos = norm_coords[i]

    def de_normalize(self):
        coords = [atom.pos for atom in self._atoms]
        denorm_coords = de_normalize_coords(coords, self.norm_factor)

        size = len(self._atoms)
        for i in range(size):
            self._atoms[i].pos = denorm_coords[i]

    @staticmethod
    def read(in_file_name, format, use_chains=False, babel_bond=False, ignore_hy=False, remove_hy=False, ignore_symm=False, use_mass=False, keep_center=False):
        #note: useMass is used when creating molecule, even though it is actually about creating the normalization
        #second note: keepCenter has only ever been tested as false, it's not at all certain it's still used or still works when true

        #step one: get the molecule object
        mol= read_file(in_file_name, format, babel_bond, ignore_symm, use_mass)

        #step two: create equivalency groups
        mol.process_equivalency(remove_hy, ignore_hy)

        #step three: save normalization data
        mol.normalize(keep_center)

        return mol