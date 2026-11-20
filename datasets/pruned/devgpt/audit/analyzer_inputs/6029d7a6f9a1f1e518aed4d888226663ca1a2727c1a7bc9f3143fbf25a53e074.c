void ssmap_path_create(const struct ssmap *m, int start_id, int end_id) {
    double distances[m->nr_nodes];
    int predecessors[m->nr_nodes];
    bool visited[m->nr_nodes];
    for(int i = 0; i < m->nr_nodes; i++) {
        distances[i] = DBL_MAX;
        predecessors[i] = -1;
        visited[i] = false;
    }
    distances[start_id] = 0;
    MinHeap *heap = create_min_heap(m->nr_nodes);
    min_heap_insert(heap, start_id, 0);
    while(!is_min_heap_empty(heap)) {
        HeapNode minNode = min_heap_extract_min(heap);
        int currentNode = minNode.node_id;
        if(visited[currentNode]) continue;
        visited[currentNode] = true;
        struct node currentNodeStruct = m->nodes[currentNode];
        for(int i = 0; i < currentNodeStruct.num_ways; i++) {
            struct way currentWay = m->ways[currentNodeStruct.way_ids[i]];
            for(int j = 0; j < currentWay.num_nodes; j++) {
                int neighborNode = currentWay.node_ids[j];
                if(visited[neighborNode]) continue;
                double travelTime = calculate_travel_time(currentNodeStruct, m->nodes[neighborNode], currentWay.speed_limit);
                double newDistance = distances[currentNode] + travelTime;
                if(newDistance < distances[neighborNode]) {
                    distances[neighborNode] = newDistance;
                    predecessors[neighborNode] = currentNode;
                    min_heap_insert(heap, neighborNode, newDistance);
                }
            }
        }
    }
    int path[m->nr_nodes];
    int pathSize = 0;
    for(int at = end_id; at != -1; at = predecessors[at]) {
        path[pathSize++] = at;
    }
    for(int i = pathSize - 1; i >= 0; i--) {
        printf("%d ", path[i]);
    }
    printf("\n");
}