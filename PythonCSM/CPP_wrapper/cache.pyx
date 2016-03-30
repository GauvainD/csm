import math
import numpy as np

cdef class Vector3D
cdef class Matrix3D

cdef Vector3D cross_product(a, b):
    '''
    :param a: length 3 vector
    :param b: length 3 vector
    :return: length 3 vector, cross product of a and b
    '''
    cdef double out[3]
    out[0] = a[1] * b[2] - a[2] * b[1]
    out[1] = a[2] * b[0] - a[0] * b[2]
    out[2] = a[0] * b[1] - a[1] * b[0]
    return Vector3D.buffer_copy(out)

cdef double inner_product(a,b):
    '''
    :param a: length 3 vector
    :param b: length 3 vector
    :return: single number, inner product of a and b
    '''
    cdef double res= a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
    return res


cdef Matrix3D outer_product_sum(a, b):
    '''
    :param a: length 3 vector
    :param b: length 3 vector
    :return: 3 x3 matrix, the outer sum of a and b plus the outer sum of b and a
    '''
    cdef double out[3][3]
    cdef int i,j
    for i in range(3):
        for j in range(3):
            out[i][j]=a[i]*b[j] + b[i]*a[j]
    return Matrix3D.buffer_copy(out)

cdef class Cache:
    cdef _cross
    cdef _outer
    cdef _inner
    def __init__(self, mol):
        size=len(mol.atoms)
        self._cross= {}
        self._outer = {}
        self._inner={}
        cdef int i, j
        for i in range(size):
            for j in range(size):
                self._cross[(i,j)]= cross_product(mol.Q[i],mol.Q[j])
                self._inner[(i,j)]= inner_product(mol.Q[i],mol.Q[j])
                self._outer[(i,j)]= outer_product_sum(mol.Q[i],mol.Q[j])

    cpdef double inner_product(Cache self, int i, int j):
        return self._inner[(i,j)]

    cpdef Matrix3D outer_product_sum(Cache self, int i, int j):
        return self._outer[(i,j)]

    cpdef Vector3D cross(Cache self, int i, int j):
        return self._cross[(i,j)]
