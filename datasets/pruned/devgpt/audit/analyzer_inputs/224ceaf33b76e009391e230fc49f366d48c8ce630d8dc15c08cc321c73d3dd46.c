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
    int *A = shmat(shmidA, NULL, 0);
    int *B = shmat(shmidB, NULL, 0);
    int *C = shmat(shmidC, NULL, 0);
    for (int i = 0; i < N*N; i++) {
        A[i] = rand() % 100;
        B[i] = rand() % 100;
        C[i] = 0;
    }
    clock_t start, end;
    double cpu_time_used;
    start = clock();
    for (int i = 0; i < N; i++) {
        pid_t pid = fork();
        if (pid == 0) {
            multiplyRowByMatrix(A, B, C, N, i);
            shmdt(A);
            shmdt(B);
            shmdt(C);
            exit(0);
        }
    }
    while (wait(NULL) > 0);
    end = clock();
    cpu_time_used = ((double) (end - start)) / CLOCKS_PER_SEC;
    printf("%d, %f\n", N, cpu_time_used);
    shmdt(A);
    shmdt(B);
    shmdt(C);
    shmctl(shmidA, IPC_RMID, NULL);
    shmctl(shmidB, IPC_RMID, NULL);
    shmctl(shmidC, IPC_RMID, NULL);
    return 0;
}