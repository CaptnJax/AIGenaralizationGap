int main() {
    int64_t value;
    int64_t *p = &value;
    if (scanf("%" SCNd64, p) == 1) {
        printf("Value: %" PRId64 "\n", value);
    } else {
        printf("Input error\n");
    }
    return 0;
}