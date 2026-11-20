std::string generateOutput(const std::vector<Recipe>& recipes) {
    std::ostringstream rawStringStream;
    rawStringStream << "{\n";
    for (size_t i = 0; i < recipes.size(); ++i) {
        rawStringStream << removeQuotes(recipes[i].getName()) << '\n'
                        << removeQuotes(recipes[i].getIngredients()) << "\n\n";
    }
    rawStringStream << "}\n";
    return rawStringStream.str();
}