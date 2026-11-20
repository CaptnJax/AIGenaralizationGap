static void test_queue_thread_safety() {
    struct prot_queue q;
    int buffer[TEST_BUF_SIZE];
    pthread_t threads[2];
    assert(prot_queue_init(&q, buffer, sizeof(buffer), sizeof(int)) == 1);
    for (int i = 0; i < 2; i++) {
        pthread_create(&threads[i], NULL, thread_func, &q);
    }
    for (int i = 0; i < 2; i++) {
        pthread_join(threads[i], NULL);
    }
    int data;
    assert(prot_queue_try_pop(&q, &data) == 0);
}