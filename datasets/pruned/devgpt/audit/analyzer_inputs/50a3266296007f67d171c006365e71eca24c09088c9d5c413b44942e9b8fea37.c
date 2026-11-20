void fillMatrix(int **matrix, int N, int isRandom) {
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            matrix[i][j] = isRandom ? rand() % 100 : 0;
        }
    }
}