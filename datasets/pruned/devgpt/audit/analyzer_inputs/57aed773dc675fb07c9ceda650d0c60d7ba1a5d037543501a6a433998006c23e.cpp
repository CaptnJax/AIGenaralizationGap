int main() {
    entt::registry registry;
    for (int i = 0; i < 10; ++i) {
        auto entity = registry.create();
    }
    registry.clear();
    return 0;
}