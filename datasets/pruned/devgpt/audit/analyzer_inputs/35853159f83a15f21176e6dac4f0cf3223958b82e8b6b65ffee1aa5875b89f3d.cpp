int main() {
    Time t1(1, 30, 45);
    Time t2(0, 45, 15);
    Time t3 = t1 + t2;
    std::cout << "t1 + t2: " << t3 << std::endl;
    Time t4 = t1 + 1000;
    std::cout << "t1 + 1000 seconds: " << t4 << std::endl;
    return 0;
}