int main() {
    int server_socket;
    struct sockaddr_in server_addr, client_addr;
    socklen_t client_addr_size = sizeof(client_addr);
    uint32_t number;
    int flag, c;
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
        recvfrom(server_socket, &number, sizeof(uint32_t), 0, (struct sockaddr *)&client_addr, &client_addr_size);
        uint32_t bigEndianData = ntohl(number);
        printf("Client: %x\n", bigEndianData);
        do {
            flag = 0;
            printf("Server (You): ");
            if (!scanf("%x", &number)) {
                printf("숫자를 입력하세요.");
                flag = 1;
                while ((c = getchar()) != '\n' && c != EOF);
            }
            number = htonl(number);
        } while (flag);
        sendto(server_socket, &number, sizeof(uint32_t), 0, (const struct sockaddr *)&client_addr, client_addr_size);
    }
    close(server_socket);
    return 0;
}