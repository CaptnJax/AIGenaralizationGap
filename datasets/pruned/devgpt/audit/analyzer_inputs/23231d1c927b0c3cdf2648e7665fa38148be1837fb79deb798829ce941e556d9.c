static void test_queue_boundary_conditions() {
    struct prot_queue q;
    int buffer[TEST_BUF_SIZE];
    int data;
    assert(prot_queue_init(&q, buffer, sizeof(buffer), sizeof(int)) == 1);
    for (int i = 0; i < TEST_BUF_SIZE; i++) {
        assert(prot_queue_push(&q, &i) == 1);
    }
    int old_head = q.head;
    int old_tail = q.tail;
    int old_count = q.count;
    assert(prot_queue_push(&q, &data) == 0);
    assert(old_head == q.head);
    assert(old_tail == q.tail);
    assert(old_count == q.count);
    for (int i = 0; i < TEST_BUF_SIZE; i++) {
        assert(prot_queue_try_pop(&q, &data) == 1);
    }
    old_head = q.head;
    old_tail = q.tail;
    old_count = q.count;
    assert(prot_queue_try_pop(&q, &data) == 0);
    assert(old_head == q.head);
    assert(old_tail == q.tail);
    assert(old_count == q.count);
}