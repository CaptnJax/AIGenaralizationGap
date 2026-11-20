int main() {
    std::vector<int> arr = {1, 2, 4, 7, 10, 11, 7, 12, 6, 7, 16, 18, 19};
    std::pair<int, int> result = findSubSortIndices(arr);
    if (result.first == -1 && result.second == -1) {
        std::cout << "The array is already sorted." << std::endl;
    } else {
        std::cout << "Indices to sort the array: (" << result.first << ", " << result.second << ")" << std::endl;
    }
    return 0;
}