bool DFS(std::unordered_map<std::string, vertex<std::string>>& map,
         std::unordered_map<std::string, std::vector<std::string>>& keys) {
    std::unordered_map<std::string, bool> visited;
    std::string room = "MainHall";
    visited[room] = true;
    std::string current;
    auto currentIt = map[room].begin();
    current = *currentIt;
    while (current != "Exit") {
        room = crossEdges(current, map, keys, visited);
        if (room == "End")
            break;
        if (!keys[room].empty()) {
            map[keys[room][0]].addEdge(keys[room][1]);
            map[keys[room][1]].addEdge(keys[room][0]);
            currentIt = map[keys[room][0]].begin();
            keys[room].clear();
        } else {
            currentIt = map[room].begin();
        }
        current = *currentIt;
    }
    return current == "Exit";
}