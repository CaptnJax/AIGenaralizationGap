int main() {
    int svgWidth = 200;
    int svgHeight = 200;
    int rectWidth = 120;
    int rectHeight = 80;
    std::ofstream svgFile;
    openSVGFile(svgFile, "output.svg", svgWidth, svgHeight);
    writeRect(svgFile, rectWidth, rectHeight, "blue");
    closeSVGFile(svgFile);
    return 0;
}