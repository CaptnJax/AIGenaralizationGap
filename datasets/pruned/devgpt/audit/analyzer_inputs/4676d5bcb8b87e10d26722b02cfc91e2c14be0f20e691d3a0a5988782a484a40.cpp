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
    double lineX1 = 312.0;
    double lineY1 = 624.0;
    double lineX2 = 408.0;
    double lineY2 = 528.0;
    std::string lineStrokeColor = "purple";
    double lineStrokeWidth = 5;
    std::string markerId = "Arrow1Sstart";
    std::ofstream svgFile;
    openSVGFile(svgFile, "output.svg", svgWidth, svgHeight);
    writeRect(svgFile, rectWidth, rectHeight, "blue");
    writeCircle(svgFile, circleCX, circleCY, circleRadius, circleStrokeColor, circleFillColor, circleStrokeWidth);
    writeMarker(svgFile, markerId);
    writeLine(svgFile, lineX1, lineY1, lineX2, lineY2, lineStrokeColor, lineStrokeWidth, markerId);
    closeSVGFile(svgFile);
    return 0;
}