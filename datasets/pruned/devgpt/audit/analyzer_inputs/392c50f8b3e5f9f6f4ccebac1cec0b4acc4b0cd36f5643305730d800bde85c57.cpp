std::pair<int, int> findSubSortIndices(const std::vector<int>& arr) {
    int n = arr.size();
    int left = 0;
    while (left < n - 1 && arr[left] <= arr[left + 1]) {
        left++;
    }
    if (left == n - 1) {
        return std::make_pair(-1, -1);
    }
    int right = n - 1;
    while (right > 0 && arr[right] >= arr[right - 1]) {
        right--;
    }
    int min_in_unsorted = *std::min_element(arr.begin() + left, arr.begin() + right + 1);
    int max_in_unsorted = *std::max_element(arr.begin() + left, arr.begin() + right + 1);
    while (left >= 0 && arr[left] > min_in_unsorted) {
        left--;
    }
    while (right < n && arr[right] < max_in_unsorted) {
        right++;
    }
    return std::make_pair(left + 1, right - 1);
}