void sortBi(BigramDictionary& dict) {
    std::sort(dict.bigrams, dict.bigrams + dict.numberOfElements, compareBigrams);
}