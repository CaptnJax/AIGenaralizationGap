int main() {
    const int numThreads = 5;
    boost::thread threads[numThreads];
    for (int i = 0; i < numThreads; ++i) {
        threads[i] = boost::thread(threadFunction, i);
    }
    for (int i = 0; i < numThreads; ++i) {
        threads[i].join();
    }
    std::cout << "All threads have finished executing" << std::endl;
    return 0;
}