void runAStarAlgorithm(std::vector<Node>& openSet, std::vector<Node>& closedSet, const int puzzle[4][4]) {
    Node start(puzzle);
    start.gScore = 0;
    start.hScore = start.calcHeuristic();
    start.fScore = start.gScore + start.hScore;
    start.prev = -1;
    openSet.push_back(start);
    std::make_heap(openSet.begin(), openSet.end(), compare());
    while (!openSet.empty()) {
        Node current = openSet[0];
        if (isgoalstate(current.matrix)) {
            break;
        }
        std::pop_heap(openSet.begin(), openSet.end());
        openSet.pop_back();
        closedSet.push_back(current);
        int parentIndex = closedSet.size() - 1;
        if (current.blankRow > 0) {
            applyOperator(current, parentIndex, openSet, closedSet, [](Node& node) { node.UP(); });
        }
        if (current.blankRow < 3) {
            applyOperator(current, parentIndex, openSet, closedSet, [](Node& node) { node.DOWN(); });
        }
        if (current.blankColumn != 0) {
            applyOperator(current, parentIndex, openSet, closedSet, [](Node& node) { node.LEFT(); });
        }
        if (current.blankColumn != 3) {
            applyOperator(current, parentIndex, openSet, closedSet, [](Node& node) { node.RIGHT(); });
        }
    }
}