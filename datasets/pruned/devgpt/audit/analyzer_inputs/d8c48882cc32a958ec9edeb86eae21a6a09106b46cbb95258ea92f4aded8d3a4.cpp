int main() {
    std::vector<int> arr1 = {4, 1, 2, 1, 1, 2};
    std::vector<int> arr2 = {3, 6, 3, 3};
    std::pair<int, int> result = findSumSwapPair(arr1, arr2);
    if (result.first != -1 && result.second != -1) {
        std::cout << "Output: {" << result.first << ", " << result.second << "}\n";
    } else {
        std::cout << "No such pair found.\n";
    }
    return 0;
}