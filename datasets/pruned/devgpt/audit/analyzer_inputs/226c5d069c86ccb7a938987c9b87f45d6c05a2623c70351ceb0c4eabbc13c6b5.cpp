TBuffer TBuffer::copy(QPoint& P1, QPoint& P2)
{
    TBuffer slice(mpHost);
    slice.clear();
    const int y = P1.y();
    int x = P1.x();
    if (y < 0 || y >= static_cast<int>(buffer.size())) {
        return slice;
    }
    if (x < 0 || x >= static_cast<int>(buffer.at(y).size())) {
        x = 0;
    }
    int P2x_corrected = std::min(P2.x(), static_cast<int>(buffer.at(y).size()) - 1);
    int oldLinkId{}, id{};
    for (; x <= P2x_corrected; ++x) {
        const int linkId = buffer.at(y).at(x).linkIndex();
        if (linkId && (linkId != oldLinkId)) {
            id = slice.mLinkStore.addLinks(mLinkStore.getLinksConst(linkId), mLinkStore.getHintsConst(linkId), mpHost);
            oldLinkId = linkId;
        }
        if (!linkId) {
            id = 0;
        }
        const QString s(lineBuffer.at(y).at(x));
        slice.append(s, 0, 1, buffer.at(y).at(x).mFgColor, buffer.at(y).at(x).mBgColor, buffer.at(y).at(x).mFlags, id);
    }
    return slice;
}