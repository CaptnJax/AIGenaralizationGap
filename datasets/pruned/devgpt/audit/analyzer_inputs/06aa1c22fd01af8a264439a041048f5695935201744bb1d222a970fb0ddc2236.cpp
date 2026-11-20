int main() {
    std::ofstream svgFile("output.svg");
    if (!svgFile.is_open()) {
        std::cerr << "Error opening file!" << std::endl;
        return 1;
    }
    Point2D tail(100.0, 200.0);
    Point2D head(300.0, 400.0);
    std::string strokeColor = "blue";
    draw_vector(svgFile, tail, head, strokeColor);
    svgFile.close();
    return 0;
}