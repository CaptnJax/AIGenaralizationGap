void check_socket_buffer_size(int sockfd) {
    int snd_size;
    int rcv_size;
    socklen_t optlen = sizeof(snd_size);
    if (getsockopt(sockfd, SOL_SOCKET, SO_SNDBUF, &snd_size, &optlen) < 0) {
        perror("getsockopt SO_SNDBUF failed");
    } else {
        std::cout << "Send buffer size: " << snd_size << " bytes" << std::endl;
    }
    if (getsockopt(sockfd, SOL_SOCKET, SO_RCVBUF, &rcv_size, &optlen) < 0) {
        perror("getsockopt SO_RCVBUF failed");
    } else {
        std::cout << "Receive buffer size: " << rcv_size << " bytes" << std::endl;
    }
}