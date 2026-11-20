int main()
{
    double list[ARRAY_SIZE] = {3.5, 1.6, -4.9, 2.5};
    double minimum, maximum;
    findMinMax(list, ARRAY_SIZE, minimum, maximum);
    cout << "Minimum: " << minimum << endl;
    cout << "Maximum: " << maximum << endl;
    return 0;
}