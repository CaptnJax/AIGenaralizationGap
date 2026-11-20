void findSubstrings(std::unordered_map<std::string, int>& substringCounts, std::unordered_map<std::string, int> wordList,
                    const std::string& targetString, int startIndex, int wordLength, const std::string& currentSubstring) {
    if (startIndex + wordLength > targetString.size()) return;
    std::string foundWord = targetString.substr(startIndex, wordLength);
    if (wordList.find(foundWord) != wordList.end()) {
        std::string newSubstring = currentSubstring + foundWord;
        wordList[foundWord]--;
        if (wordList[foundWord] == 0) {
            wordList.erase(foundWord);
        }
        if (wordList.empty()) {
            substringCounts[newSubstring]++;
        } else {
            findSubstrings(substringCounts, wordList, targetString, startIndex + wordLength, wordLength, newSubstring);
        }
    }
}