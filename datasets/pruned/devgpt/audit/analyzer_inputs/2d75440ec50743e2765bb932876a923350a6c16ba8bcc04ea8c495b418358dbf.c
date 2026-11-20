pthread_t* allocate_threads(size_t num_threads) {
    pthread_t* threads = (pthread_t*)calloc(num_threads, sizeof(pthread_t));
    if(!threads) {
        fprintf(stderr, "[ERROR]: Could not allocate space for threads\n");
        exit(1);
    }
    return threads;
}