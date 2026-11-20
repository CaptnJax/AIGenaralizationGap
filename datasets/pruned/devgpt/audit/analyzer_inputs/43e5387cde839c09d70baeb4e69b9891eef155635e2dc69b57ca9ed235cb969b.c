int main() {
    struct sigaction sa, current_sa;
    int pipefd[2];
    char buf;
    if (pipe(pipefd) == -1) {
        exit(18);
    }
    sa.sa_handler = signal_handler;
    sa.sa_flags = SA_RESETHAND;
    sigemptyset(&sa.sa_mask);
    if (sigaction(SIGINT, &sa, NULL) == -1) {
        exit(10);
    }
    if (sigaction(SIGINT, NULL, &current_sa) == -1) {
        exit(11);
    }
    if (current_sa.sa_handler != signal_handler) {
        exit(12);
    }
    if ((current_sa.sa_flags & SA_RESETHAND) != SA_RESETHAND) {
        exit(17);
    }
    pid_t pid = fork();
    if (pid == -1) {
        exit(13);
    } else if (pid == 0) {
        close(pipefd[0]);
        read(pipefd[0], &buf, 1);
        kill(getppid(), SIGINT);
        exit(EXIT_SUCCESS);
    } else {
        close(pipefd[1]);
        write(pipefd[1], "r", 1);
        pause();
        if (!handler_invoked) {
            exit(14);
        }
        if (sigaction(SIGINT, NULL, &current_sa) == -1) {
            exit(15);
        }
        if (current_sa.sa_handler != SIG_DFL) {
            exit(16);
        }
        exit(EXIT_SUCCESS);
    }
}