bool isRedundant(std::string word, std::vector<std::string>& ladder)
{
    for (auto begin = ladder.begin(); begin != ladder.end(); begin++) {
        if (word.compare(*begin) == 0) {
            return true;
        }
    }
    return false;
}