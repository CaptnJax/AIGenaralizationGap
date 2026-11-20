int main() {
    int client_socket;
    struct sockaddr_in server_addr;
    if ((client_socket = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        perror("socket creation failed");
        exit(EXIT_FAILURE);
    }
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(PORT);
    if (inet_pton(AF_INET, SERVER_IP, &server_addr.sin_addr) <= 0) {
        perror("Invalid address/ Address not supported");
        exit(EXIT_FAILURE);
    }
    int number;
    while (1) {
        printf("Client (You): ");
        scanf("%d", &number);
        sendto(client_socket, &number, sizeof(int), 0,
               (const struct sockaddr *)&server_addr, sizeof(server_addr));
        recvfrom(client_socket, &number, sizeof(int), 0, NULL, NULL);
        printf("Server: %d\n", number);
    }
    close(client_socket);
    return 0;
}