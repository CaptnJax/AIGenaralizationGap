HWND GetHWNDFromQMdiSubWindow(QMdiSubWindow* subWindow)
{
    if (subWindow) {
        QWidget* widget = subWindow->widget();
        if (widget) {
            WId wid = widget->winId();
            if (wid != 0) {
                HWND hWnd = reinterpret_cast<HWND>(wid);
                return hWnd;
            }
        }
    }
    return nullptr;
}