int main() {
    int sockfd;
    struct sockaddr_in dest_addr;
    char packet[4096];
    sockfd = socket(AF_INET, SOCK_RAW, IPPROTO_RAW);
    if (sockfd < 0) {
        perror("Socket creation failed");
        exit(EXIT_FAILURE);
    }
    memset(&dest_addr, 0, sizeof(dest_addr));
    dest_addr.sin_family = AF_INET;
    dest_addr.sin_addr.s_addr = inet_addr(DEST_IP);
    struct my_protocol_header *my_header = (struct my_protocol_header *)packet;
    my_header->field1 = htons(12345);
    my_header->field2 = htonl(54321);
    if (sendto(sockfd, packet, sizeof(struct my_protocol_header), 0, (struct sockaddr *)&dest_addr, sizeof(dest_addr)) < 0) {
        perror("Sendto failed");
        exit(EXIT_FAILURE);
    }
    printf("Packet sent successfully.\n");
    close(sockfd);
    return 0;
}