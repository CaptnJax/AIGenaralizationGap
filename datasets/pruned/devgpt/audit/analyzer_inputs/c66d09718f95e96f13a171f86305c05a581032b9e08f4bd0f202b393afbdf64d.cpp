stack<string> _88MPH(unordered_map<string, list<edge>> mapOfChargingStations, unordered_map<string, double> chargingStation, string startingLocation, double initialBattery){
    stack<string> stationPath;
    string stationName = "";
    double currentBattery = initialBattery;
    double decreaseBattery = 0.0;
    double currentDistance = 0.0;
    double charge = chargingStation[startingLocation];
    if(currentBattery <= 0.0)
        return {};
    currentBattery = currentBattery + charge;
    if(currentBattery > 75.5)
        return {};
    if(currentBattery >= 62.5 && currentBattery <= 75.5){
        stationPath.push(startingLocation);
        return stationPath;
    }
    for(auto& neighbor : mapOfChargingStations[startingLocation]){
        stationName = neighbor.station;
        currentDistance = neighbor.distance;
        decreaseBattery = currentDistance * 0.346;
        stationPath = _88MPH(mapOfChargingStations, chargingStation, stationName, currentBattery-decreaseBattery);
        if(!stationPath.empty()){
            stationPath.push(startingLocation);
            break;
        }
    }
    return stationPath;
}