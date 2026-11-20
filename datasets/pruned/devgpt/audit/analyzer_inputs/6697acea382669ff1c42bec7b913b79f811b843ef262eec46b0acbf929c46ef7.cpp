std::pair<std::string, int> getMonthAndDay(int dayOfYear) {
    std::tm timeIn = {0, 0, 0,
                      1, 0,
                      100};
    timeIn.tm_yday = dayOfYear - 1;
    std::mktime(&timeIn);
    std::string monthNames[] = {"January", "February", "March", "April", "May", "June",
                                "July", "August", "September", "October", "November", "December"};
    return {monthNames[timeIn.tm_mon], timeIn.tm_mday};
}