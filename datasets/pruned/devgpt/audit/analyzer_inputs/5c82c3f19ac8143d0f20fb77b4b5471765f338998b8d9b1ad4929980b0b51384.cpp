int main() {
    const int screenWidth = 800;
    const int screenHeight = 600;
    InitWindow(screenWidth, screenHeight, "Random Circles");
    SetTargetFPS(60);
    while (!WindowShouldClose()) {
        BeginDrawing();
        ClearBackground(RAYWHITE);
        for (int i = 0; i < 50; ++i) {
            int posX = GetRandomValue(0, screenWidth);
            int posY = GetRandomValue(0, screenHeight);
            Color circleColor = Color{GetRandomValue(200, 255), GetRandomValue(200, 255), GetRandomValue(200, 255), 255};
            int radius = GetRandomValue(10, 50);
            DrawCircle(posX, posY, radius, circleColor);
        }
        EndDrawing();
    }
    CloseWindow();
    return 0;
}