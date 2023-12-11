
cdef extern from "FastCPPUtils.h":
    int rpoly(double *coeffs, int degree, double *zeror, double *zeroi);
    void GetEigens(const double matrix[3][3], double eigenVectors[3][3], double eigenValues[3]);
    void GetEigens2D(const double matrix[3][3], double v1[3], double v2[3],
                     double eigenVectors[2][2], double eigenValues[2]);

    void GramSchmidt(double matrix[3][3]);
