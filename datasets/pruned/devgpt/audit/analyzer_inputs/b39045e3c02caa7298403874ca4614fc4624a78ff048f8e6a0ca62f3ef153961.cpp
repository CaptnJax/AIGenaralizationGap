int main() {
  Agraph_t* graph = agopen("FSM", Agdirected, nullptr);
  Agnode_t* state1 = agnode(graph, "State1", true);
  Agnode_t* state2 = agnode(graph, "State2", true);
  Agnode_t* state3 = agnode(graph, "State3", true);
  Agedge_t* transition1 = agedge(graph, state1, state2, nullptr, true);
  Agedge_t* transition2 = agedge(graph, state2, state3, nullptr, true);
  Agedge_t* transition3 = agedge(graph, state3, state1, nullptr, true);
  agsafeset(transition1, "label", "Event1", "");
  agsafeset(transition2, "label", "Event2", "");
  agsafeset(transition3, "label", "Event3", "");
  FILE* file = fopen("fsm.dot", "w");
  agwrite(graph, file);
  fclose(file);
  agclose(graph);
  return 0;
}