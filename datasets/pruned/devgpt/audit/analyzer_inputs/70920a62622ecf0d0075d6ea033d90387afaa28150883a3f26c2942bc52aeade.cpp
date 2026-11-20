int main() {
    int arr[] = {64, 25, 12, 22, 11};
    int n = sizeof(arr) / sizeof(arr[0]);
    efficientSelectionSort(arr, n);
    std::cout << "Sorted array: \n";
    printArray(arr, n);
    return 0;
}