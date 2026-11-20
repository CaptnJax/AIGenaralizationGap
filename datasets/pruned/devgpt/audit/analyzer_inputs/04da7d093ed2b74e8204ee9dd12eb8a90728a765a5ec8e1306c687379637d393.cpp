int main() {
    fHMMCpp::FluxusHMM hmm("photon_data_file.txt");
    hmm.analyze();
    return 0;
}