int main() {
    int rows = 10;
    int cols = 5;
    double **matrix = (double **)malloc(rows * sizeof(double *));
    for (int i = 0; i < rows; i++) {
        matrix[i] = (double *)malloc(cols * sizeof(double));
    }
    free_matrix(matrix, rows);
    return 0;
}