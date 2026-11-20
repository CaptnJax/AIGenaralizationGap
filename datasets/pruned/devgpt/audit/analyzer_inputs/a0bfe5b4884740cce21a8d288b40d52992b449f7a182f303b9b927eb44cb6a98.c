int main() {
    int client_socket;
    struct sockaddr_in server_addr;
    socklen_t server_addr_size = sizeof(server_addr);
    char buffer[BUFFER_SIZE];
    if ((client_socket = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        perror("socket creation failed");
        exit(EXIT_FAILURE);
    }
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(PORT);
    if (inet_pton(AF_INET, SERVER_IP, &server_addr.sin_addr) <= 0) {
        perror("inet_pton failed");
        exit(EXIT_FAILURE);
    }
    while (1) {
        printf("Client (You): ");
        if (!fgets(buffer, sizeof(buffer), stdin)) {
            printf("입력 오류가 발생하였습니다.\n");
            continue;
        }
        buffer[strcspn(buffer, "\n")] = '\0';
        int send_result = sendto(client_socket, buffer, strlen(buffer), 0, (const struct sockaddr *)&server_addr, server_addr_size);
        if (send_result < 0) {
            perror("sendto failed");
            continue;
        }
        ssize_t received_bytes = recvfrom(client_socket, buffer, sizeof(buffer), 0, NULL, NULL);
        if (received_bytes < 0) {
            perror("recvfrom failed");
            continue;
        }
        printf("Server: ");
        for (ssize_t i = 0; i < received_bytes; i++) {
            printf("%02x ", (unsigned char)buffer[i]);
        }
        printf("\n");
    }
    close(client_socket);
    return 0;
}