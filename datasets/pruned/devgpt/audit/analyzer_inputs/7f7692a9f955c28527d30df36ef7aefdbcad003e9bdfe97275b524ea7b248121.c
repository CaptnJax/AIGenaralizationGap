void freeMatrix(int ***matrix, int N) {
    for (int i = 0; i < N; i++) {
        free((*matrix)[i]);
    }
    free(*matrix);
}