int main(int argc, char *argv[]) {
    int N;
    if (argc < 2) {
        N = 10;
        printf("N value not provided, setting <N> to: %d\n", N);
    } else {
        N = atoi(argv[1]);
    }
    int isPrinted;
    if (argc < 3) {
        isPrinted = 0;
    } else {
        isPrinted = atoi(argv[2]);
    }
    srand(time(NULL));
    int **A = (int **)malloc(N * sizeof(int *));
    int **B = (int **)malloc(N * sizeof(int *));
    int **C = (int **)malloc(N * sizeof(int *));
    for (int i = 0; i < N; i++) {
        A[i] = (int *)malloc(N * sizeof(int));
        B[i] = (int *)malloc(N * sizeof(int));
        C[i] = (int *)calloc(N, sizeof(int));
    }
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            A[i][j] = rand() % 100;
            B[i][j] = rand() % 100;
        }
    }
    clock_t start, end;
    double cpu_time_used;
    start = clock();
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            for (int k = 0; k < N; k++) {
                C[i][j] += A[i][k] * B[k][j];
            }
        }
    }
    end = clock();
    cpu_time_used = ((double) (end - start)) / CLOCKS_PER_SEC;
    if(isPrinted) {
        printf("Matrix A:\n");
        printMatrix(A, N);
        printf("\n\n");
        printf("Matrix B:\n");
        printMatrix(B, N);
        printf("\n\n\n");
        printf("Resulting Matrix C (A*B):\n");
        printMatrix(C, N);
    } else {
        printf("%d, %f\n", N, cpu_time_used);
    }
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