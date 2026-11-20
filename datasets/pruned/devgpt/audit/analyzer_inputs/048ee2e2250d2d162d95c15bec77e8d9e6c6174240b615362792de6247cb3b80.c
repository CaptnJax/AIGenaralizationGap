int main() {
    int A[N][N], B[N][N], C[N][N];
    pid_t pids[N];
    int status;
    srand(time(NULL));
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            A[i][j] = rand() % 10;
            B[i][j] = rand() % 10;
        }
    }
    for (int i = 0; i < N; i++) {
        pids[i] = fork();
        if (pids[i] < 0) {
            perror("Fork falló");
            exit(EXIT_FAILURE);
        } else if (pids[i] == 0) {
            multiplyRowByMatrix(A[i], B, C[i]);
            exit(EXIT_SUCCESS);
        }
    }
    for (int i = 0; i < N; i++) {
        waitpid(pids[i], &status, 0);
    }
    printf("Matriz resultante C (A*B):\n");
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            printf("%d\t", C[i][j]);
        }
        printf("\n");
    }
    return 0;
}