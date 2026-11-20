int main(int argc, char* argv[])
{
    std::vector<std::string> wordBank;
    std::vector<std::string> ladder;
    std::ifstream inFile;
    std::string word, target;
    int status = 0;
    if (argc != 2) {
        status = 1;
    } else {
        inFile.open(argv[1]);
        while (!inFile.eof()) {
            std::string input;
            inFile >> input;
            wordBank.push_back(input);
            if (inFile.eof())
                break;
        }
        std::cin >> word >> target;
        ladder.push_back(word);
        bool found = false;
        int past_size = -1;
        while (!found) {
            found = wordLadder(word, target, wordBank, ladder);
            if (found) {
                break;
            } else {
                if (past_size == ladder.size()) {
                    std::cout << "Solution Does Not Exist\n";
                    break;
                }
                ladder.pop_back();
                past_size = ladder.size();
            }
        }
        if (ladder.back() != target)
            ladder.clear();
        if (!ladder.empty())
            for (auto word : ladder)
                std::cout << word << '\n';
    }
    return 0;
}