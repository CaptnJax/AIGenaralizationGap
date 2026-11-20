int main() {
    struct sigaction sa, current_sa;
    sa.sa_handler = signal_handler;
    sa.sa_flags = SA_RESETHAND;
    sigemptyset(&sa.sa_mask);
    if (sigaction(SIGINT, &sa, NULL) == -1) {
        exit(10);
    }
    if (sigaction(SIGINT, NULL, &current_sa) == -1) {
        exit(11);
    }
    if (current_sa.sa_handler != signal_handler || current_sa.sa_flags != SA_RESETHAND) {
        exit(12);
    }
    pid_t pid = fork();
    if (pid == -1) {
        exit(13);
    } else if (pid == 0) {
        sleep(1);
        kill(getppid(), SIGINT);
        exit(EXIT_SUCCESS);
    } else {
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