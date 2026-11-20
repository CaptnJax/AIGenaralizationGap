void displaySubstrings(const std::unordered_map<std::string, int>& substringCounts) {
    for (const auto& pair : substringCounts) {
        std::cout << pair.first << " - Count: " << pair.second << '\n';
    }
}