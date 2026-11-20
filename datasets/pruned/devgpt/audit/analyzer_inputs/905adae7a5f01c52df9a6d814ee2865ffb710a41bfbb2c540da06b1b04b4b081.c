void initializeAndFillMatrix(int ***matrix, int N, int isZero) {
    *matrix = (int **)malloc(N * sizeof(int *));
    for (int i = 0; i < N; i++) {
        (*matrix)[i] = (int *)malloc(N * sizeof(int));
        for (int j = 0; j < N; j++) {
            (*matrix)[i][j] = isZero ? 0 : rand() % 100;
        }
    }
}