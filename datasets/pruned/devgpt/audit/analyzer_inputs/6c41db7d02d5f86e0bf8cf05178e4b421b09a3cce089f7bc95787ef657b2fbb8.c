int main(int argc, char *argv[]) {
    int N = 0, verbose = 0, numProcesses = MAX_PROCESSES;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-v") == 0 || strcmp(argv[i], "--verbose") == 0) {
            verbose = 1;
        } else if (i == 1) {
            N = atoi(argv[i]);
        } else if (i == 2) {
            numProcesses = atoi(argv[i]);
        }
    }
    if (N == 0) {
        printf("Usage: %s <N> [num_processes] [-v|--verbose]\n", argv[0]);
        return 1;
    }
    numProcesses = (N < numProcesses) ? N : numProcesses;
    if (verbose) {
        printf("Matrix A:\n");
        printMatrix(A, N);
        printf("\nMatrix B:\n");
        printMatrix(B, N);
        printf("\nResult Matrix C:\n");
        printMatrix(C, N);
    }
    return 0;
}