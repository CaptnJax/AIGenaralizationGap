int main() {
    struct sigaction sa;
    pid_t pid;
    sa.sa_handler = signal_handler;
    sa.sa_flags = SA_RESETHAND;
    sigemptyset(&sa.sa_mask);
    if (sigaction(SIGINT, &sa, NULL) == -1) {
        exit(EXIT_FAILURE);
    }
    pid = fork();
    if (pid == -1) {
        exit(EXIT_FAILURE);
    } else if (pid == 0) {
        sleep(1);
        kill(getppid(), SIGINT);
        exit(EXIT_SUCCESS);
    } else {
        pause();
        exit(EXIT_FAILURE);
    }
}