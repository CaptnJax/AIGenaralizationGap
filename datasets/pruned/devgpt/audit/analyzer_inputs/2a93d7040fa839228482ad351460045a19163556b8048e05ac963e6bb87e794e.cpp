void set_socket_buffer_size(int sockfd, int size) {
    if (setsockopt(sockfd, SOL_SOCKET, SO_SNDBUF, &size, sizeof(size)) < 0) {
        perror("setsockopt SO_SNDBUF failed");
    }
    if (setsockopt(sockfd, SOL_SOCKET, SO_RCVBUF, &size, sizeof(size)) < 0) {
        perror("setsockopt SO_RCVBUF failed");
    }
}