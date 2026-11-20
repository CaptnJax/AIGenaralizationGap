int main() {
    std::unordered_map<std::string, int> wordFrequencyMap;
    std::unordered_map<std::string, int> substringCountMap;
    std::cout << "Enter target string: ";
    std::string targetString;
    std::cin >> targetString;
    std::cout << "Enter list of words (type 'END' to finish):\n";
    std::string word;
    while (std::cin >> word && word != "END") {
        wordFrequencyMap[word]++;
    }
    if (wordFrequencyMap.empty()) {
        std::cout << "Word list is empty.\n";
        return 0;
    }
    int wordLength = wordFrequencyMap.begin()->first.size();
    std::cout << "List of substrings:\n";
    findSubstrings(substringCountMap, wordFrequencyMap, targetString, 0, wordLength);
    if (substringCountMap.empty()) {
        std::cout << "No substrings found.\n";
    } else {
        displaySubstrings(substringCountMap);
    }
    return 0;
}