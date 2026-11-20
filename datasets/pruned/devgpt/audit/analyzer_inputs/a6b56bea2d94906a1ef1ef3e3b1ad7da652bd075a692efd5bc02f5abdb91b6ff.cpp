std::string generateOutput(const std::vector<std::string>& individualMembers) {
    std::ostringstream rawStringStream;
    rawStringStream << "{\n";
    for (size_t i = 0; i < individualMembers.size(); ++i) {
        std::string nameOutput = getRecipeName(individualMembers[i]);
        std::string ingredientsOutput = getIngredients(individualMembers[i]);
        rawStringStream << removeQuotes(nameOutput) << '\n' << removeQuotes(ingredientsOutput) << "\n\n";
    }
    rawStringStream << "}\n";
    return rawStringStream.str();
}