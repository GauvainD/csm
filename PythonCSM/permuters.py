import itertools
import colorama

__author__ = 'zmbq'

from CPP_wrapper import csm

colorama.init()

# Utility functions
def apply_perm(array, perm):
    result = [0] * len(array)
    for i, p in enumerate(perm):
        result[i] = array[perm[i]]
    return result

def perm_order(perm):
    start = list(range(-len(perm), 0))
    p = apply_perm(start, perm)
    order = 1
    while p!=start:
        p = apply_perm(p, perm)
        order += 1
    return order

def cycle_decomposition(perm):
    unvisited = set(range(len(perm)))  # All indices are unvisited
    def find_cycle(start):
        cycle = [start]
        next = perm[start]
        while next!=start:
            cycle.append(next)
            unvisited.remove(next)
            next = perm[next]
        return cycle

    cycles = []
    while unvisited:
        start = unvisited.pop()
        cycle = find_cycle(start)
        if len(cycle) > 1:
            cycles.append(cycle)

    return cycles

def display_perms(prefix, perms):
    for i, perm in enumerate(perms):
        print("%s %4d: %s\torder=%d\tcycles=%s" % (prefix, i, perm, perm_order(perm), cycle_decomposition(perm)))

# Perm generation functions
#
# perm_size: Size of permutation
# cycle_sizes: a list of legal cycle sizes
# cycle_structs: A list of cycles in a permutation: [[0], [1, 3, 4], [2], ...]

def get_cycle_structs(perm_size, cycle_sizes):
    def generate(cycles, left):
        len_left = len(left)
        if len_left == 0:
            yield cycles
            return

        for cycle_size in cycle_sizes:
            if cycle_size > len_left:
                break
            start = [left[0]]
            for rest in itertools.combinations(left[1:], cycle_size-1):
                cycle = start + list(rest)
                new_left = [item for item in left if item not in cycle]
                yield from generate(cycles+[cycle], new_left)

    yield from generate([], list(range(perm_size)))

def all_circles(elements):
    """ Returns all the circles (full cycles) of elements (e0->e1->e2->e3...->e0) and the trivial cycle """

    def all_circle_indices(size):
        # To compute a full cycle of length n, we take a permutation p of size n-1 and
        # create the cycle like so: 0 goes to p[0], p[0] to p[1], p[1] to p[2] and so on, until p[n-1] goes back to 0
        # For this to work, p needs to be a permutation of 1..n-1.
        #
        # For example, size = 3 we have p=(1,2) for the cycle 0->1->2->0 and p=(2,1) for the cycle 0->2->1->0
        trivial = tuple(range(1, size))
        for cycle in itertools.permutations(trivial):
            full_cycle = [0] * size
            cur = 0
            for element in cycle:
                full_cycle[cur] = cur = element
            full_cycle[cycle[-1]] = 0
            yield full_cycle

    # yield elements  # Trivial circle
    for cycle_indices in all_circle_indices(len(elements)):
        circle = tuple(elements[i] for i in cycle_indices)
        yield circle

def all_perms_from_cycle_struct(perm_size, cycle_struct):
    trivial = list(range(perm_size))

    def generate(perm, cycle_struct, cycles_left):
        if not cycles_left:
            if perm != trivial:
                #print("%s: %s" % (cycle_struct, perm))
                yield tuple(perm)
            return

        cycle = cycles_left[0]
        cycles_left = cycles_left[1:]
        if len(cycle) > 1:
            start_perm = perm[:]
            for circle in all_circles(cycle):
                for i in range(len(circle)):
                    perm[cycle[i]] = circle[i]
                yield from generate(perm, cycle_struct, cycles_left)
                perm = start_perm[:]
        else:
            yield from generate(perm, cycle_struct, cycles_left)

    yield from generate(trivial[:], cycle_struct, cycle_struct)


def get_permutations(perm_size, group_size, add_groups_of_two):
    cycle_lengths = {1, group_size}
    if add_groups_of_two:
        cycle_lengths.add(2)
    cycle_lengths = sorted(cycle_lengths)

    yield tuple(range(perm_size)) # The identity permutation first
    for cycle_struct in get_cycle_structs(perm_size, cycle_lengths):
        yield from all_perms_from_cycle_struct(perm_size, cycle_struct)


def compare(perm_size, group_size, add_groups_of_two):
    csm_perms = list(csm.GetPermutations(perm_size, group_size, add_groups_of_two))
    our_perms = list(get_permutations(perm_size, group_size, add_groups_of_two))

    allowed_cycles = {1, group_size}
    if add_groups_of_two:
        allowed_cycles.add(2)

    print("C++ permutations: %d, Python permutations: %d, unique Python: %d" % (len(csm_perms), len(our_perms), len(set(our_perms))))

    if set(csm_perms)==set(our_perms):
        return

    print("There are problems!!!")
    print("Our permutations:")
    for i, perm in enumerate(our_perms):
        cycles = cycle_decomposition(perm)
        bad_cycle = bad_perm = duplicate = False
        for cycle_size in cycles:
            if not len(cycle_size) in allowed_cycles:
                bad_cycle = True
        if not perm in csm_perms:
            bad_perm = True
        if i > 0 and perm in our_perms[:i-1]:
            duplicate = True

        print("%s %4d: %s\torder=%d\tcycles=%s" % ("Py ", i, perm, perm_order(perm), cycle_decomposition(perm)), end='')
        if bad_perm or bad_cycle:
            print(colorama.Fore.LIGHTRED_EX, end='')
            if bad_cycle:
                print('   BAD CYCLE', end='')
            elif bad_perm:
                print('   NOT IN C++', end='')
            elif duplicate:
                print('   DUPLICATE', end='')
        print(colorama.Fore.RESET)


    #print()
    #print("C++ permutations")
    for i, perm in enumerate(csm_perms):
        bad_perm = not perm in our_perms
        print("%s %4d: %s\torder=%d\tcycles=%s" % ("C++", i, perm, perm_order(perm), cycle_decomposition(perm)), end='')
        if bad_perm:
            print(colorama.Fore.LIGHTRED_EX + "   NOT IN PYTHON" + colorama.Fore.RESET, end='')
        print()

#print(list(all_circles((2,3))))
compare(12, 5, True)
# print(list(all_circles((0,1,2,3))))
# print (list(all_perms_from_cycle_struct(4, [[0,1], [2,3]])))
