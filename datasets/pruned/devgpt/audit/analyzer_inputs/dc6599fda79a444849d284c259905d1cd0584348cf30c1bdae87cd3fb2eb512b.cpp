int main() {
    srand(time(0));
    vector<int> arr;
    int n = 10;
    for (int i = 0; i < n; i++) {
        arr.push_back(rand() % 100);
    }
    quicksort(arr, 0, n - 1);
    for (int i = 0; i < n; i++) {
        cout << arr[i] << " ";
    }
    cout << endl;
    return 0;
}