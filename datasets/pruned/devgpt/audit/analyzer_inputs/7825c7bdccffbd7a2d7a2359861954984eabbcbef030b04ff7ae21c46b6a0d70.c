int main() {
    int **A, **B, **C;
    for (int i = 0; i < N; i++) {
        pid_t pid = fork();
        if (pid == 0) {
            exit(0);
        }
    }
    while (wait(NULL) > 0);
    return 0;
}