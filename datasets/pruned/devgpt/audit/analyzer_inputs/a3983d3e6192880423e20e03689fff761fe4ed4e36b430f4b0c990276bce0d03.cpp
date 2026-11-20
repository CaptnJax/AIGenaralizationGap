void strongConnectIterative(const std::vector<NodeType>& node1Data, const std::vector<NodeType>& node2Data, const std::vector<LinkType>& link1, const std::vector<LinkType>& nextLink1, std::vector<Couple<NodeType>>& indices, NodeType& currIndex, sequence_traits<Bool>::container_type& onStackFlag, NodeStackType& nodeStack, std::vector<PartType>& resSubData, PartType& nrParts, std::vector<Couple<PartType>>& partLinks) {
    struct Frame {
        NodeType node;
        LinkType currentLink;
        bool isFirstVisit;
        std::set<NodeType> successors;
    };
    std::vector<Frame> stack;
    stack.push_back({startNode, link1[startNode], true});
    while (!stack.empty()) {
        auto& frame = stack.back();
        auto& [v, currentLink, isFirstVisit, successors] = frame;
        if (isFirstVisit) {
            indices[v] = {currIndex, currIndex};
            ++currIndex;
            nodeStack.push_back(v);
            onStackFlag[v] = true;
            isFirstVisit = false;
        }
        if (IsDefined(currentLink)) {
            NodeType w = node2Data[currentLink];
            if (!IsDefined(indices[w].first)) {
                successors.insert(w);
                stack.push_back({w, link1[w], true});
            } else {
                if (onStackFlag[w]) {
                    indices[v].second = std::min(indices[v].second, indices[w].first);
                }
            }
            currentLink = nextLink1[currentLink];
        } else {
            for (auto succ : successors) {
                indices[v].second = std::min(indices[v].second, indices[succ].second);
            }
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