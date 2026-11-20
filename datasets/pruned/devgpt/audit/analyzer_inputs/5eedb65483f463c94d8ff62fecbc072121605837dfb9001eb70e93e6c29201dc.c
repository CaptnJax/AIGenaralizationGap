int main(int argc, char *argv[]) {
    int N = 0, verbose = 0, numProcessors = 2;
    getCommands(argc, argv, &N, &verbose, &numProcessors);
    int **A, **B, **C;
    allocateMatrices(&A, &B, &C, N);
    fillMatrices(A, B, C, N);
    int rowsPerProcessor = N / numProcessors;
    int pipefd[numProcessors][2];
    for (int i = 0; i < numProcessors; i++) {
        if (pipe(pipefd[i]) == -1) {
            perror("pipe");
            exit(EXIT_FAILURE);
        }
        pid_t pid = fork();
        if (pid == -1) {
            perror("fork");
            exit(EXIT_FAILURE);
        } else if (pid == 0) {
            close(pipefd[i][0]);
            int startRow = i * rowsPerProcessor;
            int endRow = (i + 1) * rowsPerProcessor;
            if (i == numProcessors - 1) endRow = N;
            int *resultChunk = (int *)malloc(rowsPerProcessor * N * sizeof(int));
            multiplyChunk(A, B, resultChunk, N, startRow, endRow);
            write(pipefd[i][1], resultChunk, rowsPerProcessor * N * sizeof(int));
            close(pipefd[i][1]);
            free(resultChunk);
            exit(0);
        }
        close(pipefd[i][1]);
    }
    for (int i = 0; i < numProcessors; i++) {
        int startRow = i * rowsPerProcessor;
        int endRow = (i + 1) * rowsPerProcessor;
        if (i == numProcessors - 1) endRow = N;
        read(pipefd[i][0], &C[startRow][0], (endRow - startRow) * N * sizeof(int));
        close(pipefd[i][0]);
        wait(NULL);
    }
    if (verbose) {
        printMatrices(A, B, C, N);
        printf("Time Clock to process: %f", cpu_time_used);
    } else {
        printf("%d, %f\n", N, cpu_time_used);
    }
    freeMatrices(A, B, C, N);
    return 0;
}