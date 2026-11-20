std::string engInt(const int& n) {
    if (n == 0) {
        return "Zero";
    }
    std::string scale[] = {"", "Thousand", "Million", "Billion"};
    std::vector<std::string> groups;
    int num = n;
    int i = 0;
    while (num > 0) {
        int threeDigits = num % 1000;
        if (threeDigits != 0) {
            groups.push_back(convertThreeDigits(threeDigits) + scale[i]);
        }
        num /= 1000;
        i++;
    }
    std::string result;
    for (int j = groups.size() - 1; j >= 0; j--) {
        result += groups[j] + " ";
    }
    return result;
}