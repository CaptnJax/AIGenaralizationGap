int main(int argc, char** argv)
{
    QCoreApplication app(argc, argv);
    CustomEventFilter eventFilter;
    app.installNativeEventFilter(&eventFilter);
    return app.exec();
}