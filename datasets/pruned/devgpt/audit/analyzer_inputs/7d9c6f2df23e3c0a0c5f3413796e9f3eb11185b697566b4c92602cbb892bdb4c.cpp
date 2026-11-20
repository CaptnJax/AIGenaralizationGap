std::string crossEdges(const std::string& current,
                       std::unordered_map<std::string, vertex<std::string>>& map,
                       std::unordered_map<std::string, std::vector<std::string>>& keys,
                       std::unordered_map<std::string, bool>& visited) {
    visited[current] = true;
    if (!keys[current].empty())
        return current;
    for (auto& neighbor : map[current]) {
        if (!visited[neighbor]) {
            std::string result = crossEdges(neighbor, map, keys, visited);
            if (result != "End")
                return result;
        }
    }
    return "End";
}