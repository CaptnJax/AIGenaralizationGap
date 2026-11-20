void findMinMax(const double arr[], int size, double& min, double& max)
{
    min = max = arr[0];
    for (int i = 1; i < size; ++i)
    {
        if (arr[i] < min)
            min = arr[i];
        if (arr[i] > max)
            max = arr[i];
    }
}