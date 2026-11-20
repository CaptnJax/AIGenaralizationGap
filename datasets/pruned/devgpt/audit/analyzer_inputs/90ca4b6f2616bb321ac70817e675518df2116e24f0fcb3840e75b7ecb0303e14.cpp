void findMinMax(double list[], double& minimum, double& maximum)
{
    for (int i = 1; i < ARRAY_SIZE; i++)
    {
        if (list[i] < minimum) {
            minimum = list[i];
        }
        else if (list[i] > maximum)
        {
            maximum = list[i];
        }
    }
}