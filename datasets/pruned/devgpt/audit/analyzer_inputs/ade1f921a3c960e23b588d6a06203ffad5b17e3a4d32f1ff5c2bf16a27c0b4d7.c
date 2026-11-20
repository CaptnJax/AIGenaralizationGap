void allocateSharedMatrix(int *shmid, int N) {
    *shmid = shmget(IPC_PRIVATE, N * N * sizeof(int), IPC_CREAT | 0666);
    if (*shmid < 0) {
        perror("shmget");
        exit(1);
    }
}