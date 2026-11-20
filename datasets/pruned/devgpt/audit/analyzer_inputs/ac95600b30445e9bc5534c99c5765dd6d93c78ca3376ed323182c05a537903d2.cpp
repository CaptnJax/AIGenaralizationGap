int main() {
    srand(static_cast<unsigned int>(time(nullptr)));
    TargetDummy dummy(100);
    int damagePerHit = 20;
    int ticks = 0;
    while (dummy.isAlive()) {
        dummy.takeDamage(damagePerHit);
        ticks++;
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        std::cout << "Tick " << ticks << ": Dummy Health: " << dummy.health << std::endl;
    }
    std::cout << "Target dummy killed in " << ticks << " ticks." << std::endl;
    return 0;
}