/*
 * Implementation of the math wrapper routines
 *
 * Written by Itay Zandbank
 */

#include "math_wrappers.h"
#include <iostream>
#include <vector>
#include <complex>
#include <cmath>
#include <Eigen/Dense>
#include <Eigen/Eigenvalues>

#if EIGEN_WORLD_VERSION==3 && EIGEN_MAJOR_VERSION==3 && EIGEN_MINOR_VERSION < 3
#error Unsupported Eigen Version, please upgrade to Eigen 3.3.3 or newer
#endif
// from rpoly.c Jenkins-Traub Polynomial Solver
extern "C" {
	int rpoly(double *op, int degree, double *zeror, double *zeroi);
}

/*
 * Find the roots of a polynomial specified by coefficients.
 * coefficients[0] is the coefficient of the highest degree, coefficients[1] of the second
 * highest and so on.
 *
 * This function delegates the calculations to rpoly.c
 */
std::vector<std::complex<double> > FindPolyRoots(const std::vector<double>& coefficients)
{
	// Prepare all the rpoly arguments
	// Allocate all the necessary memory manually, and copy the coefficients, since rpoly
	// might change them - who knows.
	size_t highest_degree = coefficients.size() - 1;
	double *zeror = new double[highest_degree];  // Not using std::vector<double>.data() because it just seems wrong
	double *zeroi = new double[highest_degree];  // although it is quite acceptable http://stackoverflow.com/questions/18759692/stdvector-write-directly-to-the-internal-array
	double *coeffs = new double[highest_degree + 1];

	for (int i = 0; i < highest_degree + 1; i++)
		coeffs[i] = coefficients[i];

	rpoly(coeffs, highest_degree, zeror, zeroi);
		
	delete[] coeffs;

	std::vector<std::complex<double> > roots;
	for (int i = 0; i < highest_degree; i++)
		roots.push_back(std::complex<double>(zeror[i], zeroi[i]));

	delete[] zeror;
	delete[] zeroi;

	return roots;
}


/*
 * Return the eigenvectors and eigenvalues of a 3x3 matrix.
 *
 * CSM only uses 3x3 matrices, so there was no point in supporting other matrix sizes.
 *
 * This is a thin wrapper around Eigen's EigenSolver.
 */

std::vector<EigenResult> GetEigens(const double matrix[3][3])
{
	//this function is not called by the python code
	Eigen::Matrix3d m;
	for (int i = 0; i < 3; i++)
		for (int j = 0; j < 3; j++)
		{
			m(i, j) = matrix[i][j];
		}

	Eigen::EigenSolver<Eigen::Matrix3d> solver(m, true);
	std::vector<EigenResult> results(3);
	for (int i = 0; i < 3; i++)
	{
		results[i].value = solver.eigenvalues()[i].real();
		results[i].vector.resize(3);
		for (int j = 0; j < 3; j++)
		{
			results[i].vector[j] = solver.eigenvectors().col(i)[j].real();
		}
	}

	return results;
}

void GetEigens(const double matrix[3][3], double eigenVectors[3][3], double eigenValues[3])
{
	Eigen::Matrix3d m;
	for (int i = 0; i < 3; i++)
		for (int j = 0; j < 3; j++)
		{
			//std::cout << "matij: " << matrix[i][j] << "\n";
			m(j,i) = matrix[i][j];
			//std::cout << "mji: " << m(j,i) << "\n";
		}

	Eigen::EigenSolver<Eigen::Matrix3d> solver(m, true);

	for (int i = 0; i < 3; i++)
	{
		eigenValues[i] = solver.eigenvalues()[i].real();
		//std::cout << "eigenvalues i: " << eigenValues[i] << "\n";
		for (int j = 0; j < 3; j++)
		{
			eigenVectors[i][j] = solver.eigenvectors().col(i)[j].real();
		}
	}
}

void GramSchmidt(double m[3][3]) {
    Eigen::Vector3d vectors[3];
    for (int i = 0; i < 3; i++) {
        Eigen::Vector3d v = Eigen::Vector3d(m[i][0],m[i][1],m[i][2]);
        Eigen::Vector3d u = v;
        for (int j = 0; j < i; j++) {
            u = (u - vectors[j].dot(v) / vectors[j].dot(vectors[j]) * vectors[j]).eval();
        }
        vectors[i] = u;
    }
    for (int i = 0; i < 3; i++) {
        vectors[i] = vectors[i] / sqrt(vectors[i].dot(vectors[i]));
        for (int j = 0; j < 3; j++) {
            m[i][j] = vectors[i](j);
        }
    }
}

void GetEigens2D(const double matrix[3][3], const double v1[3], const double v2[3], double eigenVectors[2][2], double eigenValues[2])
{
	Eigen::Matrix3d m;
	for (int i = 0; i < 3; i++) {
		for (int j = 0; j < 3; j++)
		{
			//std::cout << "matij: " << matrix[i][j] << "\n";
			m(i,j) = matrix[i][j];

			//std::cout << " " << m(i,j);
		}
        //std::cout << "\n";
    }
    Eigen::Vector3d vec1(v1);
    Eigen::Vector3d vec2(v2);
    Eigen::Matrix2d newM;

    //std::cout << "vec1 " << vec1 << "\n";
    //std::cout << "vec2 " << vec2 << "\n";
    //std::cout << "vec1.T * m " << vec1.transpose()*m << "\n";
    //std::cout << "vec1.T * m * vec2 " << (vec1.transpose()*m).dot(vec2) << "\n";
    newM(0,0) = (vec1.transpose() * m * vec1)(0);
    newM(0,1) = (vec1.transpose() * m * vec2)(0);
    newM(1,0) = (vec2.transpose() * m * vec1)(0);
    newM(1,1) = (vec2.transpose() * m * vec2)(0);

	//for (int i = 0; i < 2; i++) {
	//	for (int j = 0; j < 2; j++)
	//	{
	//		std::cout << " " << newM(i,j);
	//	}
    //    std::cout << "\n";
    //}

	Eigen::EigenSolver<Eigen::Matrix2d> solver(newM, true);

	for (int i = 0; i < 2; i++)
	{
		eigenValues[i] = solver.eigenvalues()[i].real();
		//std::cout << "eigenvalues i: " << eigenValues[i] << "\n";
		for (int j = 0; j < 2; j++)
		{
			eigenVectors[i][j] = solver.eigenvectors().col(i)[j].real();
		}
	}
}

std::vector<EigenResult> GetEigens2D(const double matrix[3][3], const double v1[3], const double v2[3])
{
}
