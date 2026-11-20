int main()
{
    double list[ARRAY_SIZE] = {3.5, 1.6, -4.9, 2.5};
    double minimum = list[0];
    double maximum = list[0];
    findMinMax(list, minimum, maximum);
    cout << "Minimum: " << minimum << endl;
    cout << "Maximum: " << maximum << endl;
    return 0;
}