int main() {
    struct sigaction sa, current_sa;
    sigset_t mask, oldmask;
    sa.sa_handler = signal_handler;
    sa.sa_flags = SA_RESETHAND;
    sigemptyset(&sa.sa_mask);
    if (sigaction(SIGINT, &sa, NULL) == -1) {
        exit(10);
    }
    sigemptyset(&mask);
    sigaddset(&mask, SIGINT);
    if (sigprocmask(SIG_BLOCK, &mask, &oldmask) == -1) {
        exit(11);
    }
    pid_t pid = fork();
    if (pid == -1) {
        exit(12);
    } else if (pid == 0) {
        sleep(1);
        kill(getppid(), SIGINT);
        exit(EXIT_SUCCESS);
    } else {
        while (!handler_invoked) {
            sigsuspend(&oldmask);
        }
        if (sigaction(SIGINT, NULL, &current_sa) == -1) {
            exit(13);
        }
        if (current_sa.sa_handler != SIG_DFL) {
            exit(14);
        }
        exit(EXIT_SUCCESS);
    }
}