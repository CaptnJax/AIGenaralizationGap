bool wordLadder(std::string word, std::string wordFinal,
                const std::vector<std::string>& words,
                std::vector<std::string>& ladder)
{
    if (word == wordFinal) {
        return true;
    }
    std::string strcomp;
    int counter = 0;
    for (auto begin = words.begin(); begin != words.end(); begin++) {
        strcomp = *begin;
        counter = 0;
        if (isRedundant(*begin, ladder)) {
            continue;
        }
        for (int i = 0; i < word.length(); i++) {
            if (word[i] == strcomp[i])
                counter++;
        }
        if (counter == word.length() - 1) {
            ladder.push_back(*begin);
            bool found = wordLadder(*begin, wordFinal, words, ladder);
            if (found) {
                return true;
            } else {
                ladder.pop_back();
            }
        }
    }
    return false;
}