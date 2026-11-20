int main() {
    int cases = 0, partyAmount = 0, voteAmount = 0;
    string filename, party, candidate, vote, winner;
    int maxVotes = 0;
    bool tie = false;
    cout << "Enter filename: ";
    cin >> filename;
    ifstream infile(filename);
    infile >> cases;
    for (int i = 0; i < cases; i++) {
        unordered_map<string, int> votes;
        unordered_map<string, string> parties;
        tie = false;
        infile >> partyAmount;
        infile.ignore();
        for (int j = 0; j < partyAmount; j++) {
            getline(infile, candidate);
            getline(infile, party);
            parties[candidate] = party;
        }
        infile >> voteAmount;
        infile.ignore();
        for (int j = 0; j < voteAmount; j++) {
            getline(infile, vote);
            votes[vote]++;
        }
        for (auto& [candidate, voteCount] : votes) {
            if (voteCount > maxVotes) {
                winner = parties[candidate];
                maxVotes = voteCount;
                tie = false;
            } else if (voteCount == maxVotes) {
                tie = true;
            }
        }
        if (tie) {
            cout << "Case " << i + 1 << " results: Tie" << endl;
        } else {
            cout << "Case " << i + 1 << " results: " << winner << endl;
        }
    }
    return 0;
}