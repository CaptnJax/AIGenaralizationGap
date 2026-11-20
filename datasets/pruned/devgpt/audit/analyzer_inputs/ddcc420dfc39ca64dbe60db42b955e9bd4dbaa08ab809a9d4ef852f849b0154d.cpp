void printArray(int arr[], int size) {
    for (int i = 0; i < size; ++i) {
        std::cout << arr[i];
        if (i != size - 1)
            std::cout << " ";
    }
    std::cout << std::endl;
}