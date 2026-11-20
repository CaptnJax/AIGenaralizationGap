static void test_queue_init_pop_push() {
    struct prot_queue q;
    int buffer[TEST_BUF_SIZE];
    int data;
    assert(prot_queue_init(&q, buffer, sizeof(buffer), sizeof(int)) == 1);
    data = 5;
    assert(prot_queue_push(&q, &data) == 1);
    assert(prot_queue_pop(&q, &data) == 1);
    assert(data == 5);
    for (int i = 0; i < TEST_BUF_SIZE; i++) {
        assert(prot_queue_push(&q, &i) == 1);
    }
    assert(prot_queue_push(&q, &data) == 0);
    for (int i = 0; i < TEST_BUF_SIZE; i++) {
        assert(prot_queue_try_pop(&q, &data) == 1);
        assert(data == i);
    }
    assert(prot_queue_try_pop(&q, &data) == 0);
}