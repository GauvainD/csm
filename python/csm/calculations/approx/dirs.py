"""
Functions for finding the symmetry directions prior to running approx
"""
import math
import numpy as np
from csm.fast import external_get_eigens as cppeigen
from csm.input_output.formatters import csm_log as print
from csm.calculations.constants import MINDOUBLE

MIN_GROUPS_FOR_OUTLIERS = 10

class DirectionChooser:
    def __init__(self, molecule, op_type, op_order, use_best_dir=False, get_orthogonal=True, detect_outliers=False, dirs=None, fibonacci=False, num_dirs=50, *args, **kwargs):
        if dirs is not None:
            self._dirs = dirs
        elif fibonacci:
            self._dirs=self.fibonacci_sphere(num_dirs)
        else:
            self._op_type=op_type
            self._op_order=op_order
            self._dirs = self._choose_initial_directions(molecule, use_best_dir, get_orthogonal, detect_outliers,
                                        op_type)

    def _choose_initial_directions(self, molecule, use_best_dir, get_orthogonal, detect_outliers,
                                           op_type):
        # if inversion:
        # not necessary to calculate dir, use geometrical center of structure
        if self._op_type == 'CI' or (self._op_type == 'SN' and self._op_order == 2):
            initial_directions = [[1.0, 0.0, 0.0]]

        else:
            initial_directions = self.find_symmetry_directions(molecule, use_best_dir, get_orthogonal, detect_outliers,
                                                          op_type)
        return initial_directions

    def fibonacci_sphere(self, num_dirs, randomize=False):
        # https://stackoverflow.com/questions/9600801/evenly-distributing-n-points-on-a-sphere/26127012#26127012
        rnd = 1.
        # if randomize:
        #    rnd = random.random() * samples

        dirs = []
        offset = 2. / num_dirs
        increment = math.pi * (3. - math.sqrt(5.));

        for i in range(num_dirs):
            y = ((i * offset) - 1) + (offset / 2);
            r = math.sqrt(1 - pow(y, 2))

            phi = ((i + rnd) % num_dirs) * increment

            x = math.cos(phi) * r
            z = math.sin(phi) * r

            dirs.append([x, y, z])

        return dirs

    @property
    def dirs(self):
        return self._dirs

    def find_symmetry_directions(self, molecule, use_best_dir, get_orthogonal, detect_outliers, op_type):
        # get average position of each equivalence group:
        group_averages = []
        for group in molecule.equivalence_classes:
            sum = [0, 0, 0]
            for index in group:
                sum += molecule.Q[index]
            average = sum / len(group)
            group_averages.append(average)
        group_averages = np.array(group_averages)

        dirs = self.dir_fit(group_averages, use_best_dir)

        if detect_outliers and len(molecule.equivalence_classes) > MIN_GROUPS_FOR_OUTLIERS:
            dirs = self.dirs_without_outliers(dirs, group_averages, op_type, use_best_dir)
        if get_orthogonal:
            dirs = self.dirs_orthogonal(dirs)
        return dirs


    def normalize_dir(self,dir):
        dir = np.array(dir)  # lists also get sent to this function, but can't be /='d
        norm = math.sqrt(math.fabs(dir[0] * dir[0] + dir[1] * dir[1] + dir[2] * dir[2]))
        dir /= norm
        return dir

    def dir_fit(self, positions, best_dir):
        # get vector of the average position
        sum = np.einsum('ij->j', positions)
        average = sum / len(positions)

        mat = np.zeros((3, 3), dtype=np.float64, order="c")
        for pos in positions:
            for j in range(3):
                for k in range(3):
                    mat[j][k] += (pos[j] - average[j]) * (pos[k] - average[k])

        # computer eigenvalues and eigenvectors
        # lambdas - list of 3 eigenvalues of matrix (function demands them, but we won't be using them here)
        # dirs- list of 3 eigenvectors of matrix
        dirs = np.zeros((3, 3), dtype=np.float64, order="c")
        lambdas = np.zeros((3), dtype=np.float64, order="c")
        cppeigen(mat, dirs, lambdas)

        min_index=np.argmin(lambdas)
        if best_dir:
            dirs=[dirs[min_index]]


        # normalize result:
        dirs = np.array([self.normalize_dir(dir) for dir in dirs])

        return dirs

    def dirs_without_outliers(self, dirs, positions, op_type, use_best_dir):
        def compute_distance_from_line(group_avg_point, test_dir_end):
            def magnitude(point1, point2):
                vec = point2 - point1
                return math.sqrt(vec[0] * vec[0] + vec[1] * vec[1] + vec[2] * vec[2])

            def get_U(Point, LineStart, LineEnd, LineMag):
                return (((Point[0] - LineStart[0]) * (LineEnd[0] - LineStart[0])) +
                        ((Point[1] - LineStart[1]) * (LineEnd[1] - LineStart[1])) +
                        ((Point[2] - LineStart[2]) * (LineEnd[2] - LineStart[2]))) / (LineMag * LineMag)

            def get_intersect(LineStart, LineEnd, U):
                Intersection = [0, 0, 0]
                Intersection[0] = LineStart[0] + U * (LineEnd[0] - LineStart[0]);
                Intersection[1] = LineStart[1] + U * (LineEnd[1] - LineStart[1]);
                Intersection[2] = LineStart[2] + U * (LineEnd[2] - LineStart[2]);
                return Intersection

            linestart = [0, 0, 0]
            linemag = magnitude(test_dir_end, linestart)
            U = get_U(group_avg_point, linestart, test_dir_end, linemag)
            intersection = get_intersect(linestart, test_dir_end, U)
            return magnitude(group_avg_point, intersection)
        print("======================detecting outliers============================")
        more_dirs = []
        for dir in dirs:
            # 1.Find the distance of each point from the line/plane
            dists=[]
            for i in range(len(positions)):
                pos = positions[i]
                if op_type == 'CS':
                    dist = math.fabs(dir[0] * pos[0] + dir[1] * pos[1] + dir[2] * pos[2])
                else:
                    dist = compute_distance_from_line(pos, dir)
                dists.append(dist)

            # 2. Find median of the distances m
            median = np.median(np.array(dists))
            # 3. for each distance di, if di > 2*m, remove it as an outlier
            with_outliers_removed = list()
            for i in range(len(positions)):
                pos = positions[i]
                dist = dists[i]
                if not (dist / median > 2 or dist / median > 2):
                    with_outliers_removed.append(pos)
            # 4. recompute dirs
            outliers_dirs = self.dir_fit(with_outliers_removed, use_best_dir)
            more_dirs += list(outliers_dirs)
        return np.array(more_dirs)

    def dirs_orthogonal(self, dirs):
        added_dirs = list(dirs)

        for dir in dirs:
            if math.fabs(dir[0]) < MINDOUBLE:
                dir1 = [1.0, 0.0, 0.0]
                dir2 = [0.0, -dir[2], dir[1]]
            elif math.fabs(dir[1]) < MINDOUBLE:
                dir1 = [-dir[2], 0.0, dir[0]]
                dir2 = [0.0, 1.0, 0.0]
            else:
                dir1 = [-dir[1], dir[0], 0.0]
                dir2 = [0.0, -dir[2], dir[1]]
            # normalize dir1:
            dir1 = self.normalize_dir(dir1)
            # remove projection of dir1 from dir2
            scal = dir1[0] * dir2[0] + dir1[1] * dir2[1] + dir1[2] * dir2[2]
            dir2[0] -= scal * dir1[0]
            dir2[1] -= scal * dir1[1]
            dir2[2] -= scal * dir1[2]
            # normalize dir2
            dir2 = self.normalize_dir(dir2)
            added_dirs.append(dir1)
            added_dirs.append(dir2)

        return np.array(added_dirs)


def dirs_orthogonal(dirs):
    """
    this function is called by dircsm, and until that gets killed and moved to here, it stays
    :param dirs: 
    :return: 
    """
    dc = DirectionChooser(None, None, None, dirs=[1, 1, 1])
    return dc.dirs_orthogonal(dirs)



class DirectionChooserNew:
    def __init__(self, molecule, chooser_type, orthogonal, num_dirs, dirs=None):
        dirs=[]
        if orthogonal:
            dirs = dirs_orthogonal(dirs)
        #remove doubles (can be introduced by orth)
        dirs=list(set(dirs))
        pass

    def classic(self):
        pass

    def atom_vectors(self):
        molecule=self.molecule
        dirs=[]
        for atom in molecule.atoms:
            dir = [atom.pos[0] - molecule.center_of_mass[0],
                   atom.pos[1] - molecule.center_of_mass[1],
                   atom.pos[2] - molecule.center_of_mass[2]]
            dir /= np.linalg.norm(dir)
            dirs.append(dir)
        return dirs

    def cube_corners(self):
        molecule=self.molecule
        dirs=[]
        center = molecule.center_of_mass
        corner = np.add(center, [.5, .5, .5])
        dirs.append(corner)
        corner = np.add(center, [.5, .5, -.5])
        dirs.append(corner)
        corner = np.add(center, [.5, -.5, .5])
        dirs.append(corner)
        corner = np.add(center, [.5, -.5, -.5])
        dirs.append(corner)
        corner = np.add(center, [-.5, .5, .5])
        dirs.append(corner)
        corner = np.add(center, [-.5, .5, -.5])
        dirs.append(corner)
        corner = np.add(center, [-.5, -.5, .5])
        dirs.append(corner)
        corner = np.add(center, [-.5, -.5, -.5])
        dirs.append(corner)
        return dirs

    def fibonacci_sphere(self, num_dirs, randomize=False):
        # https://stackoverflow.com/questions/9600801/evenly-distributing-n-points-on-a-sphere/26127012#26127012
        rnd = 1.
        #if randomize:
        #    rnd = random.random() * samples

        dirs = []
        offset = 2. / num_dirs
        increment = math.pi * (3. - math.sqrt(5.));

        for i in range(num_dirs):
            y = ((i * offset) - 1) + (offset / 2);
            r = math.sqrt(1 - pow(y, 2))

            phi = ((i + rnd) % num_dirs) * increment

            x = math.cos(phi) * r
            z = math.sin(phi) * r

            dirs.append([x, y, z])

        return dirs


