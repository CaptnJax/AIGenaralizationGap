static inline int prot_queue_init(struct prot_queue* q, void* buf, int buflen,
				  int elem_size)
{
	if (buflen == 0 || buflen % elem_size != 0)
		return 0;
	q->head = 0;
	q->tail = 0;
	q->count = 0;
	q->buf = buf;
	q->buflen = buflen;
	q->elem_size = elem_size;
	pthread_mutex_init(&q->mutex, NULL);
	pthread_cond_init(&q->cond, NULL);
	return 1;
}