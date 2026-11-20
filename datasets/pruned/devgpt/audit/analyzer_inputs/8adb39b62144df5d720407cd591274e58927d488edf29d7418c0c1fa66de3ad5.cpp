int main() {
    int svgWidth = 600;
    int svgHeight = 600;
    int rectWidth = 120;
    int rectHeight = 80;
    double circleCX = 504.2;
    double circleCY = 403.5;
    double circleRadius = 3;
    std::string circleStrokeColor = "purple";
    std::string circleFillColor = "purple";
    double circleStrokeWidth = 1;
    std::ofstream svgFile;
    openSVGFile(svgFile, "output.svg", svgWidth, svgHeight);
    writeRect(svgFile, rectWidth, rectHeight, "blue");
    writeCircle(svgFile, circleCX, circleCY, circleRadius, circleStrokeColor, circleFillColor, circleStrokeWidth);
    closeSVGFile(svgFile);
    return 0;
}