static inline int prot_queue_try_pop(struct prot_queue *q, void *data) {
	pthread_mutex_lock(&q->mutex);
	if (q->count == 0) {
		pthread_mutex_unlock(&q->mutex);
		return 0;
	}
	memcpy(data, &q->buf[q->head * q->elem_size], q->elem_size);
	q->head = (q->head + 1) % prot_queue_capacity(q);
	q->count--;
	pthread_cond_signal(&q->cond);
	pthread_mutex_unlock(&q->mutex);
	return 1;
}