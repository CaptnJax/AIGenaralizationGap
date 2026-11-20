int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("N value not provided\n");
        return -1;
    }
    int N = atoi(argv[1]);
    int **A, **B, **C;
    allocateMatrices(&A, &B, &C, N);
    fillMatrices(A, B, C, N);
    return 0;
}