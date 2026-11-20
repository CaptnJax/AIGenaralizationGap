fluxpool SimpleNbox::npp(std::string biome, double time) const {
  unitval temp = core->sendMessage(M_GETDATA, D_GLOBAL_TAS);
  double temp_double = temp.value();
  fluxpool npp(npp_flux0.at(biome).value(U_PGC_YR), U_PGC_YR);
  double temp_adjust = (1 + (0.001639 - 2 * 0.0004306 * temp_double) * (1 / (0.3761 + 0.001639 * temp_double - 0.0004306 * temp_double * temp_double)) * temp_double);
  if (time == Core::undefinedIndex()) {
      npp = npp * co2fert.at(biome) * temp_adjust;
  } else {
      npp = npp * calc_co2fert(biome, time) * temp_adjust;
  }
  npp = npp * npp_luc_adjust;
  return npp;
}