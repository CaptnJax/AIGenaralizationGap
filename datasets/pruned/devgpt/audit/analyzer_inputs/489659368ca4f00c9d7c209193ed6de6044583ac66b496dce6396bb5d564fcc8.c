int main() {
    double cadence = 55;
    double resistance = 13;
    double wattage = calculateWattage(cadence, resistance);
    printf("Predicted Wattage: %.2f Watts\n", wattage);
    return 0;
}