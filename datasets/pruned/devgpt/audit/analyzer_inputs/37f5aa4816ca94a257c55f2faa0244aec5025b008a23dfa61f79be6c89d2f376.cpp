void TTextEdit::expandSelectionToWords()
{
    int yind = mPA.y();
    int xind = mPA.x();
    if (yind >= 0 && yind < static_cast<int>(mpBuffer->lineBuffer.size())) {
        for (; xind >= 0; --xind) {
            if (xind < static_cast<int>(mpBuffer->lineBuffer.at(yind).size())) {
                QChar currentChar = mpBuffer->lineBuffer.at(yind).at(xind);
                if (currentChar == QChar::Space
                    || mpHost->mDoubleClickIgnore.contains(currentChar)) {
                    break;
                }
            } else {
                break;
            }
        }
    }
    mDragStart.setX(xind + 1);
    mPA.setX(xind + 1);
    yind = mPB.y();
    xind = mPB.x();
    if (yind >= 0 && yind < static_cast<int>(mpBuffer->lineBuffer.size())) {
        for (; xind < static_cast<int>(mpBuffer->lineBuffer.at(yind).size()); ++xind) {
            QChar currentChar = mpBuffer->lineBuffer.at(yind).at(xind);
            if (currentChar == QChar::Space
                || mpHost->mDoubleClickIgnore.contains(currentChar)) {
                break;
            }
        }
    }
    mDragSelectionEnd.setX(xind - 1);
    mPB.setX(xind - 1);
}