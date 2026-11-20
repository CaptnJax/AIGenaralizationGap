int main() {
    SDL_FRect rect1 = { 10.5f, 20.3f, 100.7f, 100.1f };
    SDL_FRect rect2 = { 10.6f, 20.4f, 100.8f, 100.2f };
    SDL_FRect rect3 = { 10.5f, 20.3f, 100.7f, 100.1f };
    if (AreFRectsEqual(rect1, rect2)) {
    } else {
    }
    if (AreFRectsEqual(rect1, rect3)) {
    } else {
    }
    return 0;
}