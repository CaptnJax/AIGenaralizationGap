float getRandomFloat(float min, float max) {
    std::random_device rd;
    std::mt19937 eng(rd());
    std::uniform_real_distribution<float> distr(min, max);
    return distr(eng);
}