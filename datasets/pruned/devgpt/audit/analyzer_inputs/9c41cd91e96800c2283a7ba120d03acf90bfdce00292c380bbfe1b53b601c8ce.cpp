int main() {
    TargetDummy dummy(250);
    std::vector<Ability> abilities;
    abilities.push_back(Ability(15.0, 10.0, 30.0, 0.0, 2, "Fireball"));
    abilities.push_back(Ability(10.0, 5.0, 20.0, 0.0, 1, "Frostbolt"));
    abilities.push_back(Ability(20.0, 15.0, 10.0, 0.0, 3, "Lightning Strike"));
    abilities.push_back(Ability(5.0, 0.0, 0.0, 0.0, 0, "Instant Damage"));
    std::sort(abilities.begin(), abilities.end(), compareAbilities);
    int ticksPerSecond = 10;
    int ticks = 0;
    double elapsedTimeSeconds = 0.0;
    while (dummy.isAlive()) {
        for (Ability& ability : abilities) {
            ability.updateActivity(elapsedTimeSeconds);
            if (ability.canCast(elapsedTimeSeconds, sharedCooldown)) {
                ability.castAbility(elapsedTimeSeconds);
                sharedCooldown = sharedCooldownValue;
            }
            if (ability.canDealDamage(elapsedTimeSeconds)) {
                dummy.takeDamage(static_cast<int>(ability.damage));
                ability.lastDamageTime = elapsedTimeSeconds;
                std::cout << "Ability: " << ability.name << " Priority: " << ability.priority
                          << " Used at Tick " << ticks << " (Time: " << elapsedTimeSeconds << "s) "
                          << "Dealt " << ability.damage << " damage. Dummy Health: " << dummy.health << std::endl;
            }
        }
        elapsedTimeSeconds += 1.0 / ticksPerSecond;
        sharedCooldown -= 1.0 / ticksPerSecond;
        ticks++;
    }
    double totalElapsedTimeSeconds = static_cast<double>(ticks - 1) / ticksPerSecond;
    std::cout << "Target dummy killed in " << totalElapsedTimeSeconds << " seconds." << std::endl;
    return 0;
}