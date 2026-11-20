int main() {
    struct sigaction sa;
    sa.sa_handler = signal_handler;
    sa.sa_flags = SA_RESETHAND;
    sigemptyset(&sa.sa_mask);
    if (sigaction(SIGINT, &sa, NULL) == -1) {
        exit(EXIT_FAILURE);
    }
    pid_t pid = fork();
    if (pid == -1) {
        exit(EXIT_FAILURE);
    } else if (pid == 0) {
        sleep(1);
        kill(getppid(), SIGINT);
        exit(EXIT_SUCCESS);
    } else {
        pause();
        if (!handler_invoked) {
            exit(EXIT_FAILURE);
        }
        struct sigaction current_sa;
        if (sigaction(SIGINT, NULL, &current_sa) == -1) {
            exit(EXIT_FAILURE);
        }
        if (current_sa.sa_handler != SIG_DFL) {
            exit(EXIT_FAILURE);
        }
        exit(EXIT_SUCCESS);
    }
}