bool MyApplication::event(QEvent *event) {
    if (event->type() == QEvent::FileOpen) {
        QFileOpenEvent *openEvent = static_cast<QFileOpenEvent *>(event);
        if (openEvent->url().scheme() == "mudlet") {
            qDebug() << "Opening URL:" << openEvent->url().toString();
            return true;
        }
    }
    return QApplication::event(event);
}