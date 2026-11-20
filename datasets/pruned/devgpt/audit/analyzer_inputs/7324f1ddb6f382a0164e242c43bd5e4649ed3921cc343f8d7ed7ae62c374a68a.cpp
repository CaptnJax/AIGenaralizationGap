int findDay(const std::string& month, int index) {
    const int startingIndices[] = {0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334};
    for (int i = 0; i < 12; ++i) {
        if (month == findMonth(startingIndices[i])) {
            return index - startingIndices[i] + 1;
        }
    }
    return -1;
}