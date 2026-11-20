int main(int argc, char *argv[]) {
    if (argc < 3) {
        printf("Usage: %s <N> <num_processes>\n", argv[0]);
        return 1;
    }
    int N = atoi(argv[1]);
    int numProcesses = atoi(argv[2]);
    int chunkSize, remainingRows, startRow, endRow;
    int shmidA = shmget(IPC_PRIVATE, N * N * sizeof(int), IPC_CREAT | 0666);
    int shmidB = shmget(IPC_PRIVATE, N * N * sizeof(int), IPC_CREAT | 0666);
    int shmidC = shmget(IPC_PRIVATE, N * N * sizeof(int), IPC_CREAT | 0666);
    int *A = (int *)shmat(shmidA, NULL, 0);
    int *B = (int *)shmat(shmidB, NULL, 0);
    int *C = (int *)shmat(shmidC, NULL, 0);
    srand(time(NULL));
    for (int i = 0; i < N * N; i++) {
        A[i] = rand() % 100;
        B[i] = rand() % 100;
    }
    clock_t start = clock();
    chunkSize = N / numProcesses;
    remainingRows = N % numProcesses;
    for (int i = 0; i < numProcesses; i++) {
        pid_t pid = fork();
        if (pid == 0) {
            startRow = i * chunkSize;
            endRow = (i + 1) * chunkSize + (i == numProcesses - 1 ? remainingRows : 0);
            multiplyChunk(A, B, C, N, startRow, endRow);
            shmdt(A);
            shmdt(B);
            shmdt(C);
            exit(0);
        }
    }
    for (int i = 0; i < numProcesses; i++) {
        waitpid(pid[i], NULL, 0);
    }
    clock_t end = clock();
    double cpu_time_used = ((double) (end - start)) / CLOCKS_PER_SEC;
    printf("%d, %f\n", N, cpu_time_used);
    shmdt(A);
    shmdt(B);
    shmdt(C);
    shmctl(shmidA, IPC_RMID, NULL);
    shmctl(shmidB, IPC_RMID, NULL);
    shmctl(shmidC, IPC_RMID, NULL);
    return 0;
}