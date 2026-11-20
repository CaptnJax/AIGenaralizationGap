void store_data(Data& data, int value) {
    if (value < 0) {
        size_t idx = -value / data.size();
        if (idx < data.size()) {
            data[idx] = value;
        }
    } else {
        size_t idx = value / data.size();
        if (idx < data.size()) {
            data[idx] = value;
        }
    }
}