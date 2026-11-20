void store_data(Data& data, int value) {
    size_t idx = (value % data.size() + data.size()) % data.size();
    data[idx] = value;
}