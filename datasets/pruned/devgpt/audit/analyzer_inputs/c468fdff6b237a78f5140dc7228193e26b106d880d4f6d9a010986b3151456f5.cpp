string numberToWords(int num) {
    if (num == 0) {
        return "Zero";
    }
    string scale[] = {"", "Thousand", "Million", "Billion"};
    vector<string> groups;
    int i = 0;
    while (num > 0) {
        int threeDigits = num % 1000;
        if (threeDigits != 0) {
            groups.push_back(convertThreeDigits(threeDigits) + scale[i]);
        }
        num /= 1000;
        i++;
    }
    string result;
    for (int j = groups.size() - 1; j >= 0; j--) {
        result += groups[j] + " ";
    }
    return result;
}