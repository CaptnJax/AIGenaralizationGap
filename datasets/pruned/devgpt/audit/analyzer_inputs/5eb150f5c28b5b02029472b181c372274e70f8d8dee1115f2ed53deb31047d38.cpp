int main() {
    float minValue = 1.0;
    float maxValue = 10.0;
    float randomValue = getRandomFloat(minValue, maxValue);
    std::cout << "Random float value between " << minValue << " and " << maxValue << ": " << randomValue << std::endl;
    return 0;
}