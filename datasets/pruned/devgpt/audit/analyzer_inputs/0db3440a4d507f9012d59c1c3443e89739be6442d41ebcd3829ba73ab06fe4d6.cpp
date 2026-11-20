int main() {
    int index;
    std::cout << "Enter the index (1-365): ";
    std::cin >> index;
    if (index < 1 || index > 365) {
        std::cerr << "Invalid index.\n";
        return 1;
    }
    std::string month = findMonth(index);
    int date = findDay(month, index);
    std::cout << "Month: " << month << "\n";
    std::cout << "Day in month: " << date << "\n";
    return 0;
}