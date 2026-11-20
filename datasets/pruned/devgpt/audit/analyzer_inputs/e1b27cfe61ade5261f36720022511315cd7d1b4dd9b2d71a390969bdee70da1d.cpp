int main() {
    std::vector<int> arr = {12, 11, 13, 5, 6, 7};
    std::cout << "Given array is:\n";
    printArray(arr);
    mergeSort(arr, 0, arr.size() - 1);
    std::cout << "\nSorted array is:\n";
    printArray(arr);
    return 0;
}