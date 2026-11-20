int main() {
    int server_socket;
    struct sockaddr_in server_addr, client_addr;
    socklen_t client_addr_size;
    char buffer[BUFFER_SIZE];
    if ((server_socket = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        perror("socket creation failed");
        exit(EXIT_FAILURE);
    }
    memset(&server_addr, 0, sizeof(server_addr));
    memset(&client_addr, 0, sizeof(client_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(PORT);
    server_addr.sin_addr.s_addr = INADDR_ANY;
    if (bind(server_socket, (const struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("bind failed");
        exit(EXIT_FAILURE);
    }
    printf("Server started. Waiting for messages...\n");
    while (1) {
        int len = recvfrom(server_socket, (char *)buffer, BUFFER_SIZE, 0,
                           (struct sockaddr *)&client_addr, &client_addr_size);
        buffer[len] = '\0';
        printf("Client: %s\n", buffer);
        printf("Server (You): ");
        fgets(buffer, BUFFER_SIZE, stdin);
        sendto(server_socket, (const char *)buffer, strlen(buffer), 0,
               (const struct sockaddr *)&client_addr, client_addr_size);
    }
    close(server_socket);
    return 0;
}