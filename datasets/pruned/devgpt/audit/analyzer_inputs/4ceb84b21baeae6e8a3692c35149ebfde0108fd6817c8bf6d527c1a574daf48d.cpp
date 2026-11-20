int main() {
    Point point1 = {1.0, 2.0};
    Point point2 = {4.0, 6.0};
    float distance = calculateDistance(point1, point2);
    std::cout << "Distance between point1 and point2: " << distance << std::endl;
    return 0;
}