int main() {
    int sockfd;
    struct sockaddr_in server_addr;
    char packet[4096];
    sockfd = socket(AF_INET, SOCK_RAW, IPPROTO_RAW);
    if (sockfd < 0) {
        perror("Socket creation failed");
        exit(EXIT_FAILURE);
    }
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(LISTEN_PORT);
    if (bind(sockfd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("Bind failed");
        exit(EXIT_FAILURE);
    }
    ssize_t bytes_received = recvfrom(sockfd, packet, sizeof(packet), 0, NULL, NULL);
    if (bytes_received < 0) {
        perror("Recvfrom failed");
        exit(EXIT_FAILURE);
    }
    struct my_protocol_header *received_header = (struct my_protocol_header *)packet;
    uint16_t field1 = ntohs(received_header->field1);
    uint32_t field2 = ntohl(received_header->field2);
    printf("Received custom header: field1=%u, field2=%u\n", field1, field2);
    close(sockfd);
    return 0;
}