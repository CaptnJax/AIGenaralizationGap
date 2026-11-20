int main() {
    int sockfd;
    struct sockaddr_in dest_addr;
    char *data_to_send = "Hello, this is raw binary data!";
    size_t data_len = strlen(data_to_send);
    sockfd = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (sockfd < 0) {
        perror("Socket creation failed");
        exit(EXIT_FAILURE);
    }
    memset(&dest_addr, 0, sizeof(dest_addr));
    dest_addr.sin_family = AF_INET;
    dest_addr.sin_addr.s_addr = inet_addr(DEST_IP);
    dest_addr.sin_port = htons(DEST_PORT);
    ssize_t bytes_sent = sendto(sockfd, data_to_send, data_len, 0, (struct sockaddr *)&dest_addr, sizeof(dest_addr));
    if (bytes_sent < 0) {
        perror("Sendto failed");
        exit(EXIT_FAILURE);
    }
    printf("Sent %zd bytes of raw binary data\n", bytes_sent);
    close(sockfd);
    return 0;
}