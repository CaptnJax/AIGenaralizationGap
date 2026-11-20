void ssmap_path_create(const struct ssmap *m, int start_id, int end_id) {
    double *travelTimes = malloc(m->nr_nodes * sizeof(double));
    int *predecessors = malloc(m->nr_nodes * sizeof(int));
    bool *visited = malloc(m->nr_nodes * sizeof(bool));
    int *currentBestPath = malloc(m->nr_nodes * sizeof(int));
    int currentBestPathSize = 0;
    double bestPathTime = DBL_MAX;
    MinHeap *heap = create_min_heap(m->nr_nodes);
    for (int i = 0; i < m->nr_nodes; i++) {
        travelTimes[i] = DBL_MAX;
        predecessors[i] = -1;
        visited[i] = false;
        currentBestPath[i] = -1;
        if (i == start_id) {
            min_heap_insert(heap, i, 0.0);
            travelTimes[i] = 0.0;
        } else {
            min_heap_insert(heap, i, DBL_MAX);
        }
    }
    while (!is_min_heap_empty(heap)) {
        HeapNode currentNode = min_heap_extract_min(heap);
        int currentNodeId = currentNode.node_id;
        visited[currentNodeId] = true;
        if (currentNodeId == end_id) {
            break;
        }
        struct node *currentNodePtr = &m->nodes[currentNodeId];
        for (int i = 0; i < currentNodePtr->num_ways; i++) {
            struct way *wayPtr = &m->ways[currentNodePtr->way_ids[i]];
            for (int j = 0; j < wayPtr->num_nodes; j++) {
                int neighborNodeId = wayPtr->node_ids[j];
                if (visited[neighborNodeId]) continue;
                double travelTime = calculate_travel_time(*currentNodePtr, m->nodes[neighborNodeId], wayPtr->speed_limit);
                if (travelTimes[currentNodeId] + travelTime < travelTimes[neighborNodeId]) {
                    travelTimes[neighborNodeId] = travelTimes[currentNodeId] + travelTime;
                    predecessors[neighborNodeId] = currentNodeId;
                    min_heap_decrease_key(heap, neighborNodeId, travelTimes[neighborNodeId]);
                }
            }
        }
    }
    int tempPath[m->nr_nodes];
    int tempPathSize = 0;
    for (int at = end_id; at != -1; at = predecessors[at]) {
        tempPath[tempPathSize++] = at;
    }
    double tempPathTime = ssmap_path_travel_time(m, tempPathSize, tempPath);
    if (tempPathTime < bestPathTime) {
        bestPathTime = tempPathTime;
        currentBestPathSize = tempPathSize;
        for (int i = 0; i < tempPathSize; i++) {
            currentBestPath[i] = tempPath[tempPathSize - 1 - i];
        }
    }
    for (int i = 0; i < currentBestPathSize; i++) {
        printf("%d ", currentBestPath[i]);
    }
    printf("\n");
    free(travelTimes);
    free(predecessors);
    free(visited);
    free(currentBestPath);
}