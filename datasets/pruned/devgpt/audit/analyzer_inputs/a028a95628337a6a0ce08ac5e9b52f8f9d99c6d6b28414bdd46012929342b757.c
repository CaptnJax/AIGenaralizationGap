int main() {
    uint32_t value = 0x03da0001;
    uint32_t bigEndianValue = htonl(value);
    printf("빅 엔디안 값: 0x%08x\n", bigEndianValue);
    return 0;
}