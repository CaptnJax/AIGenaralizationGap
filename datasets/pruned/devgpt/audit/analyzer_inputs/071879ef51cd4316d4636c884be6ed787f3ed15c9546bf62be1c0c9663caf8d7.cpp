void store_data(Data& data, int value) {
    int idx = value / static_cast<int>(data.size());
    if (idx >= 0 && idx < static_cast<int>(data.size())) {
        data[idx] = value;
    }
}