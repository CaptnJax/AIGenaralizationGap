int findMostAliveYear(const vector<Person>& people) {
    int years[101] = {0};
    for (const Person& p : people) {
        for (int year = p.birth; year <= p.death; ++year) {
            years[year - 1900]++;
        }
    }
    int maxAliveYear = 1900;
    int maxAliveCount = years[0];
    for (int i = 1; i < 101; ++i) {
        if (years[i] > maxAliveCount) {
            maxAliveCount = years[i];
            maxAliveYear = 1900 + i;
        }
    }
    return maxAliveYear;
}