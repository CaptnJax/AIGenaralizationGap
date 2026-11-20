int main() {
    double sharedCooldownValue = 1.0;
    int ticksPerSecond = 10;
    TargetDummy dummy(250);
    std::vector<Ability> abilities;
    abilities.push_back(Ability(15.0, 10.0, 30.0, 10.0, 2, "Firestorm"));
    abilities.push_back(Ability(10.0, 5.0, 20.0, 5.0, 1, "Frostbite"));
    abilities.push_back(Ability(20.0, 15.0, 10.0, 15.0, 3, "Thunderstrike"));
    abilities.push_back(Ability(5.0, 0.0, 0.0, 0.0, 0, "Venom Strike"));
    std::sort(abilities.begin(), abilities.end(), compareAbilities);
    int ticks = 0;
    double elapsedTimeSeconds = 0.0;
    double sharedCooldown = 0.0;
    while (dummy.isAlive()) {
        for (Ability& ability : abilities) {
            if (ability.canDealDamage(elapsedTimeSeconds)) {
                std::cout << ability.name << " used at Tick " << ticks
                          << " (Time: " << elapsedTimeSeconds << "s) - Health: " << dummy.health << std::endl;
            }
            ability.updateActivity(elapsedTimeSeconds);
            const double epsilon = 1e-5;
            if (!ability.isActive && sharedCooldown <= epsilon) {
                ability.castAbility(elapsedTimeSeconds);
                sharedCooldown = sharedCooldownValue;
            }
            if (ability.canDealDamage(elapsedTimeSeconds)) {
                dummy.takeDamage(static_cast<int>(ability.damage));
                ability.lastDamageTime = elapsedTimeSeconds;
            }
        }
        if (sharedCooldown > 0.0) {
            sharedCooldown -= 1.0 / ticksPerSecond;
        }
        elapsedTimeSeconds += 1.0 / ticksPerSecond;
        ticks++;
    }
    double totalElapsedTimeSeconds = static_cast<double>(ticks - 1) / ticksPerSecond;
    std::cout << "Target dummy killed in " << totalElapsedTimeSeconds << " seconds." << std::endl;
    return 0;
}