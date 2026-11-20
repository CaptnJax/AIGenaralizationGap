int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("N value not provided\n");
        return -1;
    }
    int N = atoi(argv[1]);
    srand(time(NULL));
    int **A, **B, **C;
    initializeAndFillMatrix(&A, N, 0);
    initializeAndFillMatrix(&B, N, 0);
    initializeAndFillMatrix(&C, N, 1);
    clock_t start = clock();
    multiplyMatrices(A, B, C, N);
    clock_t end = clock();
    double cpu_time_used = ((double) (end - start)) / CLOCKS_PER_SEC;
    printf("%d, %f\n", N, cpu_time_used);
    freeMatrix(&A, N);
    freeMatrix(&B, N);
    freeMatrix(&C, N);
    return 0;
}