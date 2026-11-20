void rotateClockwise(vector<vector<int>>& matrix) {
    int n = matrix.size();
    for (int i = 0; i < n / 2; ++i) {
        for (int j = i; j < n - i - 1; ++j) {
            matrix[j][n - 1 - i] = std::exchange(matrix[i][j], matrix[j][n - 1 - i]);
            matrix[n - 1 - i][n - 1 - j] = std::exchange(matrix[j][n - 1 - i], matrix[n - 1 - i][n - 1 - j]);
            matrix[n - 1 - j][i] = std::exchange(matrix[n - 1 - i][n - 1 - j], matrix[n - 1 - j][i]);
            matrix[i][j] = std::exchange(matrix[n - 1 - j][i], matrix[i][j]);
        }
    }
}