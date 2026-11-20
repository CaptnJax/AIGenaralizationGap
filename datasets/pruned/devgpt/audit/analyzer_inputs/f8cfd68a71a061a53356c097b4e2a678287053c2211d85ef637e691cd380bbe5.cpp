int main() {
    using namespace SNES;
    PPU::setINIDISP(0x0F, true);
    PPU::setBGMODE(1);
    PPU::setOBSEL(0, 0x10);
    return 0;
}