int main(int argc, char* argv[]) {
    CefMainArgs main_args(argc, argv);
    CefRefPtr<CefCommandLine> command_line = CefCommandLine::CreateCommandLine();
    command_line->InitFromArgv(argc, argv);
    CefInitialize(main_args, CefStructBase<CefSettings>(), nullptr, nullptr);
    CefWindowInfo window_info;
    window_info.SetAsPopup(nullptr, "DevTools");
    CefBrowserSettings browser_settings;
    CefRefPtr<DevToolsClient> devtools_client(new DevToolsClient());
    CefBrowserHost::CreateBrowser(window_info, devtools_client, "https://www.example.com", browser_settings, nullptr);
    CefRefPtr<CefBrowser> browser = devtools_client->GetBrowser();
    CefRefPtr<CefBrowserHost> browser_host = browser->GetHost();
    browser_host->ShowDevTools(window_info, devtools_client, CefBrowserSettings(), CefPoint());
    const int targetScreen = 2;
    CefRefPtr<CefDisplay> main_display = CefDisplay::GetDesktopDisplay();
    std::vector<CefRect> screen_rects;
    main_display->GetScreenInfo(screen_rects);
    if (targetScreen > 0 && targetScreen <= screen_rects.size()) {
        const CefRect& target_screen_rect = screen_rects[targetScreen - 1];
        window_info.SetAsPopup(nullptr, "DevTools", target_screen_rect.x, target_screen_rect.y, target_screen_rect.width, target_screen_rect.height);
        browser_host->WasResized();
        browser_host->NotifyMoveOrResizeStarted();
    } else {
    }
    CefRunMessageLoop();
    CefShutdown();
    return 0;
}