int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: %s <N> [-p num_processors]\n", argv[0]);
        exit(1);
    }
    int N = atoi(argv[1]);
    srand(time(NULL));
    int shmidA, shmidB, shmidC;
    allocateSharedMatrix(&shmidA, N);
    allocateSharedMatrix(&shmidB, N);
    allocateSharedMatrix(&shmidC, N);
    int **A = attachMatrix(shmidA, N);
    int **B = attachMatrix(shmidB, N);
    int **C = attachMatrix(shmidC, N);
    fillMatrix(A, N, 1);
    fillMatrix(B, N, 1);
    fillMatrix(C, N, 0);
    int numProcessors = MAX_PROCESSORS;
    int rowsPerProcessor = N / numProcessors;
    for (int p = 0; p < numProcessors; p++) {
        int startRow = p * rowsPerProcessor;
        int endRow = (p + 1) * rowsPerProcessor;
        if (p == numProcessors - 1) {
            endRow = N;
        }
        pid_t pid = fork();
        if (pid == 0) {
            multiplyMatrixChunk(A, B, C, N, startRow, endRow);
            detachMatrix(A);
            detachMatrix(B);
            detachMatrix(C);
            exit(0);
        }
    }
    while (wait(NULL) > 0);
    detachMatrix(A);
    detachMatrix(B);
    detachMatrix(C);
    shmctl(shmidA, IPC_RMID, NULL);
    shmctl(shmidB, IPC_RMID, NULL);
    shmctl(shmidC, IPC_RMID, NULL);
    return 0;
}