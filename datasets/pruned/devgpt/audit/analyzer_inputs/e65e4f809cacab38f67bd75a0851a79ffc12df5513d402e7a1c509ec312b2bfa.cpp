void strongConnectIterative(const std::vector<NodeType>& node1Data, const std::vector<NodeType>& node2Data, const std::vector<LinkType>& link1, const std::vector<LinkType>& nextLink1, std::vector<Couple<NodeType>>& indices, NodeType& currIndex, sequence_traits<Bool>::container_type& onStackFlag, NodeStackType& nodeStack, std::vector<PartType>& resSubData, PartType& nrParts) {
    struct Frame {
        NodeType node;
        LinkType currentLink;
        bool isFirstVisit;
        bool processSuccessor;
    };
    std::vector<Frame> stack;
    stack.push_back({startNode, link1[startNode], true, false});
    while (!stack.empty()) {
        auto& frame = stack.back();
        auto& [v, currentLink, isFirstVisit, processSuccessor] = frame;
        if (isFirstVisit) {
            indices[v] = {currIndex, currIndex};
            ++currIndex;
            nodeStack.push_back(v);
            onStackFlag[v] = true;
            isFirstVisit = false;
        } else if (processSuccessor) {
            NodeType w = node2Data[currentLink];
            if (onStackFlag[w]) {
                indices[v].second = std::min(indices[v].second, indices[w].first);
            }
            processSuccessor = false;
            currentLink = nextLink1[currentLink];
        }
        if (!processSuccessor && IsDefined(currentLink)) {
            NodeType w = node2Data[currentLink];
            if (!IsDefined(indices[w].first)) {
                stack.push_back({w, link1[w], true, false});
                processSuccessor = true;
            } else {
                if (onStackFlag[w]) {
                    indices[v].second = std::min(indices[v].second, indices[w].first);
                }
                currentLink = nextLink1[currentLink];
            }
        } else if (!IsDefined(currentLink)) {
            if (indices[v].first == indices[v].second) {
                NodeType w;
                do {
                    w = nodeStack.back(); nodeStack.pop_back();
                    onStackFlag[w] = false;
                    resSubData[w] = nrParts;
                } while (w != v);
                nrParts++;
            }
            stack.pop_back();
        }
    }
}