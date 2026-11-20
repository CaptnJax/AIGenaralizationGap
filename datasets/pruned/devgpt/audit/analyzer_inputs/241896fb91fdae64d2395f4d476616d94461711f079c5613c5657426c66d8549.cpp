int GetMonitorScaleFactor(HWND hWnd)
{
    HDC hdc = GetDC(hWnd);
    int logPixelsX = GetDeviceCaps(hdc, LOGPIXELSX);
    ReleaseDC(hWnd, hdc);
    if (logPixelsX == 96)
        return 100;
    else if (logPixelsX == 120)
        return 125;
    else if (logPixelsX == 144)
        return 150;
    else if (logPixelsX == 192)
        return 200;
    return 0;
}