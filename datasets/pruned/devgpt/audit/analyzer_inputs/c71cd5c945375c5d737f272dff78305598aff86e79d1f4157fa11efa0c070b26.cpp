int main() {
    vector<Person> people = {
        {1900, 1950},
        {1910, 1930},
        {1920, 1970},
    };
    int mostAliveYear = findMostAliveYear(people);
    cout << "The year with the most people alive is: " << mostAliveYear << endl;
    return 0;
}