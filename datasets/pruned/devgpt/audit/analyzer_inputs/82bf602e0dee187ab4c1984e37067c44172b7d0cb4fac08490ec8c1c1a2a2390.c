void normalize_probability(double **pheromones)
{
    double sum_dimension = 0.0;
    double prob, start;
    for (int i = 0; i < parameters.dimension; i++)
    {
        sum_dimension += sum_pheromone_dimension(pheromones, parameters.dimension);
    }
    for (int i = 0; i < parameters.dimension; i++)
    {
        start = 0.0;
        for (int j = 0; j < parameters.population_size; j++)
        {
            double pheromone = pheromones[j][i];
            if (sum_dimension != 0.0 && pheromone != 0.0) {
                prob = pheromone / sum_dimension;
                probability_interval[j][i].min = start;
                probability_interval[j][i].max = start + prob;
                start += prob;
            } else {
                probability_interval[j][i].min = 0.0;
                probability_interval[j][i].max = 0.0;
            }
        }
    }
}