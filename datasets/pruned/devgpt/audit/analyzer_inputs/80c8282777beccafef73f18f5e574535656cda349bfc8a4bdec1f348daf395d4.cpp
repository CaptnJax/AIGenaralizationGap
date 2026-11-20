int main() {
    char input;
    int Caccounts = 0;
    int Saccounts = 0;
    int count = 0;
    do {
        displayMainMenu();
        cin >> input;
        input = toupper(input);
        switch (input) {
            case 'D':
                processMoney(Caccounts, Saccounts, true, false);
                break;
            case 'W':
                processMoney(Caccounts, Saccounts, false, true);
                break;
            case 'Q':
                writeFile(                              );
                cout << "Goodbye!" << endl;
                break;
            default:
                cout << "Invalid selection. Please try again." << endl;
                break;
        }
    } while (input != 'Q');
    return 0;
}