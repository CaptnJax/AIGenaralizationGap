int GetMonitorScaleFactor(HWND hWnd)
{
    HWND hTopWnd = GetAncestor(hWnd, GA_ROOT);
    HMONITOR hMonitor = MonitorFromWindow(hTopWnd, MONITOR_DEFAULTTONEAREST);
    UINT dpiX, dpiY;
    if (GetDpiForMonitor(hMonitor, MDT_EFFECTIVE_DPI, &dpiX, &dpiY) == S_OK) {
        if (dpiX == 96)
            return 100;
        else if (dpiX == 120)
            return 125;
        else if (dpiX == 144)
            return 150;
        else if (dpiX == 192)
            return 200;
    }
    return 0;
}