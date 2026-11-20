std::pair<int, int> findSumSwapPair(std::vector<int>& arr1, std::vector<int>& arr2) {
    int sum1 = 0, sum2 = 0;
    for (int num : arr1) {
        sum1 += num;
    }
    for (int num : arr2) {
        sum2 += num;
    }
    int targetDifference = (sum1 - sum2) / 2;
    std::unordered_set<int> setArr2(arr2.begin(), arr2.end());
    for (int num : arr1) {
        int complement = num - targetDifference;
        if (setArr2.find(complement) != setArr2.end()) {
            return {num, complement};
        }
    }
    return {-1, -1};
}