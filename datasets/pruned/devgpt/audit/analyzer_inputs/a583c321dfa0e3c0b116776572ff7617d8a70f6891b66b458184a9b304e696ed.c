void multiplyRowByMatrix(int row[N], int matrix[N][N], int result[N]) {
    for (int i = 0; i < N; i++) {
        result[i] = 0;
        for (int j = 0; j < N; j++) {
            result[i] += row[j] * matrix[j][i];
        }
    }
}