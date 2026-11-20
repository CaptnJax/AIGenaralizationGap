stack<string> _88MPH(const unordered_map<string, list<edge>>& mapOfChargingStations, const unordered_map<string, double>& chargingStation, const string& startingLocation, double initialBattery) {
    stack<string> stationPath;
    if (initialBattery <= 0.0 || chargingStation.find(startingLocation) == chargingStation.end())
        return stationPath;
    double currentBattery = initialBattery + chargingStation.at(startingLocation);
    if (currentBattery > 75.5)
        return stationPath;
    if (currentBattery >= 62.5) {
        stationPath.push(startingLocation);
        return stationPath;
    }
    for (const auto& neighbor : mapOfChargingStations.at(startingLocation)) {
        double decreaseBattery = neighbor.distance * 0.346;
        stack<string> path = _88MPH(mapOfChargingStations, chargingStation, neighbor.station, currentBattery - decreaseBattery);
        if (!path.empty()) {
            path.push(startingLocation);
            return path;
        }
    }
    return stationPath;
}