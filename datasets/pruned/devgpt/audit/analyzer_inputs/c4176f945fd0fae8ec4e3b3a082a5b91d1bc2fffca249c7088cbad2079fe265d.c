static inline int prot_queue_capacity(struct prot_queue *q) {
	return q->buflen / q->elem_size;
}