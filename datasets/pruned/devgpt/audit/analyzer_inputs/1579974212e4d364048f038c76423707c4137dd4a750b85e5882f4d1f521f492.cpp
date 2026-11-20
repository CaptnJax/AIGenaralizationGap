int main() {
    std::string filename = "TextFile1.txt";
    std::string rawString = readFileIntoRawString(filename);
    removeLeadingWhitespace(rawString);
    ensureNewlineAfterBrace(rawString);
    removeLeadingWhitespace(rawString);
    std::vector<std::string> catsToRemove = { "type", "category", "enabled", "order", "allow_decomposition", "main_product", "subgroup", "requester_paste_multiplier", "icon" };
    for (const auto& category : catsToRemove) {
        removeLineStartingWith(rawString, category);
    }
    removeNewlineAfterEquals(rawString);
    std::vector<std::string> individualMembers = extractIndividualMembers(rawString);
    std::string output = generateOutput(individualMembers);
    std::cout << output;
    writeToTxtFile(output, "roughCut.txt");
    return 0;
}