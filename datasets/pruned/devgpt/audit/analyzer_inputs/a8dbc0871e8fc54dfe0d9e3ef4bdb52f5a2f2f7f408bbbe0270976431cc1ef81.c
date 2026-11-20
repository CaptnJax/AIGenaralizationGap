int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: %s <N>\n", argv[0]);
        return -1;
    }
    int N = atoi(argv[1]);
    srand(time(NULL));
    int shmidA = shmget(IPC_PRIVATE, N*N*sizeof(int), IPC_CREAT | 0666);
    int shmidB = shmget(IPC_PRIVATE, N*N*sizeof(int), IPC_CREAT | 0666);
    int shmidC = shmget(IPC_PRIVATE, N*N*sizeof(int), IPC_CREAT | 0666);
    int *shm_A = shmat(shmidA, NULL, 0);
    int *shm_B = shmat(shmidB, NULL, 0);
    int *shm_C = shmat(shmidC, NULL, 0);
    int **A = (int **)malloc(N * sizeof(int *));
    int **B = (int **)malloc(N * sizeof(int *));
    int **C = (int **)malloc(N * sizeof(int *));
    for (int i = 0; i < N; i++) {
        A[i] = shm_A + N*i;
        B[i] = shm_B + N*i;
        C[i] = shm_C + N*i;
    }
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            A[i][j] = rand() % 100;
            B[i][j] = rand() % 100;
            C[i][j] = 0;
        }
    }
    clock_t start, end;
    double cpu_time_used;
    start = clock();
    for (int i = 0; i < N; i++) {
        pid_t pid = fork();
        if (pid == 0) {
            multiplyRowByMatrix(A, B, C, N, i);
            exit(0);
        }
    }
    while (wait(NULL) > 0);
    end = clock();
    cpu_time_used = ((double) (end - start)) / CLOCKS_PER_SEC;
    printf("Matrix multiplication completed in %f seconds\n", cpu_time_used);
    shmdt(shm_A);
    shmdt(shm_B);
    shmdt(shm_C);
    shmctl(shmidA, IPC_RMID, NULL);
    shmctl(shmidB, IPC_RMID, NULL);
    shmctl(shmidC, IPC_RMID, NULL);
    free(A);
    free(B);
    free(C);
    return 0;
}