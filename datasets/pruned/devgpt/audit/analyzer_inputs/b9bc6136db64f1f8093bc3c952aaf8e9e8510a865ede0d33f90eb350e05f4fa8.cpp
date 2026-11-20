int main() {
      std::ofstream outputFile("example.txt");
      if (!outputFile.is_open()) {
          std::cerr << "Error opening file!" << std::endl;
          return 1;
      }
      outputFile << "Hello, File!\n";
      outputFile << "This is a line written to the file.";
      outputFile.close();
      return 0;
  }