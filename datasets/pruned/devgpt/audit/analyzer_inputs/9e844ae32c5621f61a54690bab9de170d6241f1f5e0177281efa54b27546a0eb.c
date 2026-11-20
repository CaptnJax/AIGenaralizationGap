int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: %s <matrix_size>\n", argv[0]);
        return -1;
    }
    int N = atoi(argv[1]);
    srand(time(NULL));
    int** A = allocateMatrix(N);
    int** B = allocateMatrix(N);
    int** C = allocateMatrix(N);
    fillMatrixWithRandomValues(A, N);
    fillMatrixWithRandomValues(B, N);
    fillMatrixWithZeros(C, N);
    for (int i = 0; i < N; i++) {
        free(A[i]);
        free(B[i]);
        free(C[i]);
    }
    free(A);
    free(B);
    free(C);
    return 0;
}