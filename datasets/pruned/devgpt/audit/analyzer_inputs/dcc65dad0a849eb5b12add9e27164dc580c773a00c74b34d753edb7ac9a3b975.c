int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("N value not provided\n");
        return -1;
    }
    int N = atoi(argv[1]);
    int **A, **B, **C;
    allocateMatrices(N, &A, &B, &C);
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