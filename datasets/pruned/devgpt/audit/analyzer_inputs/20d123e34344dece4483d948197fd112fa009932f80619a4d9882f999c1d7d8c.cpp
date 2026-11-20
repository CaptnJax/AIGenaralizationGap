int main() {
    std::string fileName;
    std::ifstream policeStationFile;
    do {
        std::cout << "Enter the police station file name: ";
        std::cin >> fileName;
        policeStationFile.open(fileName);
    } while (!policeStationFile.is_open());
    std::unordered_map<std::string, vertex<std::string>> map;
    std::string line;
    while (std::getline(policeStationFile, line)) {
        std::istringstream iss(line);
        std::string key, value;
        if (iss >> key >> value) {
            map[key].addEdge(value);
            map[value].addEdge(key);
        }
    }
    policeStationFile.close();
    std::unordered_map<std::string, std::vector<std::string>> keys;
    do {
        std::cout << "Enter the keys file name: ";
        std::cin >> fileName;
        policeStationFile.open(fileName);
    } while (!policeStationFile.is_open());
    while (std::getline(policeStationFile, line)) {
        std::istringstream iss(line);
        std::string key, value1, value2;
        if (iss >> key >> value1 >> value2) {
            keys[key].emplace_back(value1);
            keys[key].emplace_back(value2);
        }
    }
    policeStationFile.close();
    bool success = DFS(map, keys);
    if (success) {
        std::cout << "Congratulations! You escaped the police station!\n";
    } else {
        std::cout << "Unfortunately, you were unable to escape the police station.\n";
    }
    return 0;
}