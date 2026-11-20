void multiplyRowByMatrix(int **A, int **B, int **C, int N, int row) {
    for (int j = 0; j < N; j++) {
        for (int k = 0; k < N; k++) {
            C[row][j] += A[row][k] * B[k][j];
        }
    }
}