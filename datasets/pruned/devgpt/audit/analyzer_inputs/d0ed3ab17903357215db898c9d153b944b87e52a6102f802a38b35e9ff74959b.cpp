int main() {
    int dayOfYear;
    std::cout << "Enter the day of the year (1-365): ";
    std::cin >> dayOfYear;
    if (dayOfYear < 1 || dayOfYear > 365) {
        std::cerr << "Invalid day of the year.\n";
        return 1;
    }
    auto result = getMonthAndDay(dayOfYear);
    std::cout << "Month: " << result.first << "\n";
    std::cout << "Day in month: " << result.second << "\n";
    return 0;
}