void* thread_func(void* arg) {
    struct prot_queue* q = (struct prot_queue*) arg;
    int data;
    for (int i = 0; i < 100; i++) {
        data = i;
        prot_queue_push(q, &data);
        prot_queue_pop(q, &data);
    }
    return NULL;
}