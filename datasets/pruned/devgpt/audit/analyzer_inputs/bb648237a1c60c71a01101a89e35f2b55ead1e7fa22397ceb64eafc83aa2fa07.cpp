bool compareBigrams(const Bigram& bg1, const Bigram& bg2) {
    if (bg1.word1 != bg2.word1) {
        return bg1.word1 < bg2.word1;
    }
    return bg1.word2 < bg2.word2;
}