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
                break;
            case 'W':
                break;
            case 'Q':
                cout << "Goodbye!" << endl;
                break;
            default:
                cout << "Invalid selection. Please try again." << endl;
                break;
        }
    } while (input != 'Q');
    return 0;
}