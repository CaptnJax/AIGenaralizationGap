void strongConnectIterative(const std::vector<NodeType>& node1Data, const std::vector<NodeType>& node2Data, const std::vector<LinkType>& link1, const std::vector<LinkType>& nextLink1, std::vector<Couple<NodeType>>& indices, NodeType& currIndex, sequence_traits<Bool>::container_type& onStackFlag, NodeStackType& nodeStack, std::vector<PartType>& resSubData, PartType& nrParts) {
    struct Frame {
        NodeType node;
        LinkType currentLink;
        bool processSuccessor;
    };
    std::vector<Frame> stack;
    for (NodeType startNode = 0; startNode < node1Data.size(); ++startNode) {
        if (!IsDefined(indices[startNode].first)) {
            indices[startNode] = {currIndex, currIndex};
            ++currIndex;
            nodeStack.push_back(startNode);
            onStackFlag[startNode] = true;
            stack.push_back({startNode, link1[startNode], false});
            while (!stack.empty()) {
                auto& [v, currentLink, processSuccessor] = stack.back();
                if (processSuccessor) {
                    NodeType w = node2Data[currentLink];
                    indices[v].second = std::min(indices[v].second, indices[w].second);
                    processSuccessor = false;
                    currentLink = nextLink1[currentLink];
                }
                if (!processSuccessor && IsDefined(currentLink)) {
                    NodeType w = node2Data[currentLink];
                    if (!IsDefined(indices[w].first)) {
                        indices[w] = {currIndex, currIndex};
                        ++currIndex;
                        nodeStack.push_back(w);
                        onStackFlag[w] = true;
                        stack.push_back({w, link1[w], false});
                        processSuccessor = true;
                    } else {
                        processSuccessor = true;
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
    }
}