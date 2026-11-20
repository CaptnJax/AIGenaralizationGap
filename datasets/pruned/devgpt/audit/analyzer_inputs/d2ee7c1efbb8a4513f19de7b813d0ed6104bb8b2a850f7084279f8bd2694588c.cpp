int main() {
    Queue q;
    q.push(1);
    q.push(2);
    q.push(3);
    std::cout << q.peek(0) << std::endl;
    std::cout << q.peek(1) << std::endl;
    std::cout << q.peek(2) << std::endl;
    std::cout << q.pop() << std::endl;
    std::cout << q.peek(0) << std::endl;
    return 0;
}