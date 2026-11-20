void strongConnectIterative(NodeType startNode) {
    std::vector<std::tuple<NodeType, LinkType, bool>> stack;
    stack.emplace_back(startNode, UNDEFINED_VALUE(LinkType), true);
    while (!stack.empty()) {
        auto& [v, currentLink, isFirstVisit] = stack.back();
        if (isFirstVisit) {
            indices[v] = {currIndex, currIndex};
            ++currIndex;
            nodeStack.emplace_back(v);
            assert(!onStackFlag[v]);
            onStackFlag[v] = true;
            isFirstVisit = false;
            currentLink = link1[v];
        } else {
            if (IsDefined(currentLink)) {
                NodeType w = node2Data[currentLink];
                if (!IsDefined(indices[w].first)) {
                    stack.emplace_back(w, UNDEFINED_VALUE(LinkType), true);
                } else if (onStackFlag[w]) {
                }
                currentLink = nextLink1[currentLink];
            } else {
                stack.pop_back();
            }
        }
    }
}