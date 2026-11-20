int main() {
    srand(static_cast<unsigned int>(time(nullptr)));
    TargetDummy dummy(100);
    int damagePerHit = 20;
    double tickDuration = 0.1;
    int ticks = 0;
    while (dummy.isAlive()) {
        dummy.takeDamage(damagePerHit);
        ticks++;
        std::cout << "Tick " << ticks << ": Dummy Health: " << dummy.health << std::endl;
    }
    double elapsedTime = ticks * tickDuration;
    std::cout << "Target dummy killed in " << elapsedTime << " seconds." << std::endl;
    return 0;
}