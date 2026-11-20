int main() {
    struct sigaction sa, current_sa;
    sa.sa_handler = signal_handler;
    sa.sa_flags = SA_RESETHAND;
    sigemptyset(&sa.sa_mask);
    if (sigaction(SIGINT, &sa, NULL) == -1) {
        exit(1);
    }
    if (sigaction(SIGINT, NULL, &current_sa) == -1 || current_sa.sa_handler != signal_handler) {
        exit(2);
    }
    pid_t pid = fork();
    if (pid == -1) {
        exit(3);
    } else if (pid == 0) {
        sleep(1);
        kill(getppid(), SIGINT);
        exit(EXIT_SUCCESS);
    } else {
        pause();
        if (!handler_invoked) {
            exit(4);
        }
        if (sigaction(SIGINT, NULL, &current_sa) == -1 || current_sa.sa_handler != SIG_DFL) {
            exit(5);
        }
        exit(EXIT_SUCCESS);
    }
}