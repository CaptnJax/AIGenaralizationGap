int main()
{
    int numThreads = 4;
    std::vector<std::thread> threads;
    for (int i = 0; i < numThreads; ++i)
    {
        threads.emplace_back(workerFunction);
    }
    for (std::thread& thread : threads)
    {
        thread.join();
    }
    return 0;
}