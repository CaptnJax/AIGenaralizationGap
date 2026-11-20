static inline int prot_queue_push(struct prot_queue* q, void *data)
{
	int cap;
	pthread_mutex_lock(&q->mutex);
	cap = prot_queue_capacity(q);
	if (q->count == cap) {
		pthread_mutex_unlock(&q->mutex);
		return 0;
	}
	memcpy(&q->buf[q->tail * q->elem_size], data, q->elem_size);
	q->tail = (q->tail + 1) % cap;
	q->count++;
	pthread_cond_signal(&q->cond);
	pthread_mutex_unlock(&q->mutex);
	return 1;
}