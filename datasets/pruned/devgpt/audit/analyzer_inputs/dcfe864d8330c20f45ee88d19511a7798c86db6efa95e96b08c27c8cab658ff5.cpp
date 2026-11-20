int main() {
    TargetDummy dummy(250);
    std::vector<Ability> abilities;
    abilities.push_back(Ability(15.0, 10.0, 30.0, 10.0, 2, "Frostbolt"));
    abilities.push_back(Ability(10.0, 5.0, 20.0, 5.0, 1, "Fireball"));
    abilities.push_back(Ability(20.0, 15.0, 10.0, 15.0, 3, "Thunderstrike"));
    abilities.push_back(Ability(5.0, 0.0, 0.0, 0.0, 0, "Basic Attack"));
    std::sort(abilities.begin(), abilities.end(), compareAbilities);
    double sharedCooldownValue = 1.0;
    int ticksPerSecond = 10;
    int ticks = 0;
    double elapsedTimeSeconds = 0.0;
    double sharedCooldown = 0.0;
    while (dummy.isAlive()) {
        for (Ability& ability : abilities) {
            ability.isActive = false;
            if (sharedCooldown <= 0.0) {
                if (elapsedTimeSeconds - ability.lastCastTime >= ability.cooldown) {
                    ability.isActive = true;
                    ability.lastCastTime = elapsedTimeSeconds;
                    sharedCooldown = sharedCooldownValue;
                }
            }
            if (ability.isActive) {
                std::cout << "Ability with Priority " << ability.priority << " (" << ability.name << ") used at Tick " << ticks
                          << " (Time: " << elapsedTimeSeconds << "s) - Damage: " << ability.damage << std::endl;
                dummy.takeDamage(static_cast<int>(ability.damage));
                ability.lastDamageTime = elapsedTimeSeconds;
            }
        }
        if (sharedCooldown > 0.0) {
            sharedCooldown -= 1.0 / ticksPerSecond;
        }
        std::cout << "Tick " << ticks << ": Dummy Health: " << dummy.health << std::endl;
        elapsedTimeSeconds += 1.0 / ticksPerSecond;
        ticks++;
    }
    double totalElapsedTimeSeconds = static_cast<double>(ticks - 1) / ticksPerSecond;
    std::cout << "Target dummy killed in " << totalElapsedTimeSeconds << " seconds." << std::endl;
    return 0;
}