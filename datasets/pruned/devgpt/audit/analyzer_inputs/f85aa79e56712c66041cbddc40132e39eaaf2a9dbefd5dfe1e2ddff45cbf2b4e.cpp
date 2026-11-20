int main() {
    using namespace gw2combat::component;
    entt::registry registry;
    entt::registry copyRegistry;
    auto entity = registry.create();
    registry.emplace<ComponentA>(entity);
    registry.emplace<ComponentB>(entity);
    registry.emplace<ComponentC>(entity);
    registry.each([&](auto entity) {
        auto newEntity = copyRegistry.create();
        if(registry.all_of<ComponentA>(entity)) {
            copyRegistry.emplace<ComponentA>(newEntity, registry.get<ComponentA>(entity));
        }
        if(registry.all_of<ComponentB>(entity)) {
            copyRegistry.emplace<ComponentB>(newEntity, registry.get<ComponentB>(entity));
        }
        if(registry.all_of<ComponentC>(entity)) {
            copyRegistry.emplace<ComponentC>(newEntity, registry.get<ComponentC>(entity));
        }
    });
    return 0;
}