template<typename... Keys>
requires (std::same_as<Keys, KeyCode> && ...)
inline bool IsKeyDown(Keys... keys) {
    return (::IsKeyDown(KeyCodeToRaylibKey(keys)) || ...);
}