int main() {
    const int numThreads = 5;
    bdlmt::ThreadUtil::Handle threads[numThreads];
    for (int i = 0; i < numThreads; ++i) {
        threads[i].start(&threadFunction, i);
    }
    for (int i = 0; i < numThreads; ++i) {
        threads[i].join();
    }
    std::cout << "All threads have finished executing" << std::endl;
    return 0;
}