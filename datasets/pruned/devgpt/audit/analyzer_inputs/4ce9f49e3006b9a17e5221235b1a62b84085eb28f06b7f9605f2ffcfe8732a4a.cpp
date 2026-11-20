void getValidGuess(char &userguess, vector<char> userguesses, string guess, int miss)
{
    string guessedString;
    string errMsg;
    while (true)
    {
        clearScreen();
        printMan(miss);
        cout << endl;
        cout << guess << "   " << errMsg << endl;
        errMsg = "";
        cout << "Enter Guess [a ~ z]: ";
        cin >> guessedString;
        cout << endl;
        if (!isOneCharLong(guessedString))
        {
            errMsg = "Guess has to be one character long!";
        }
        else
        {
            userguess = guessedString[0];
            if (!isalpha(userguess))
            {
                errMsg = "Guess has to be an alphabet!";
            }
            else
            {
                if (guessedAlready(userguess, userguesses))
                {
                    errMsg = userguess;
                    errMsg += " has been guessed already";
                }
                else
                {
                    break;
                }
            }
        }
    }
}