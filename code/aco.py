from enviroment import Enviroment # Corrected typo: environment
from ant import Ant
# import copy # Not used
from statistics import mean, stdev
import json
# import numpy as np # Not directly used in this file

class ACO():
    def __init__(self, ALPHA_JS, ALPHA_MA, BETA, dataset, cycles, ant_numbers, 
                 init_pheromone_js, init_pheromone_ma, 
                 pheromone_constant_js, pheromone_constant_ma,
                 min_pheromone_js, min_pheromone_ma, 
                 evaporation_rate_js, evaporation_rate_ma, seed):
        
        self.ALPHA_JS = ALPHA_JS
        self.ALPHA_MA = ALPHA_MA
        self.BETA = BETA
        self.cycles = cycles
        self.ant_numbers = ant_numbers
        self.pheromone_constant_js = pheromone_constant_js
        self.pheromone_constant_ma = pheromone_constant_ma
        self.evaporation_rate_js = evaporation_rate_js
        self.evaporation_rate_ma = evaporation_rate_ma
        self.seed = seed

        # Initialize the Environment and set data
        self.enviroment = Enviroment(dataset, init_pheromone_js, init_pheromone_ma, 
                                     min_pheromone_js, min_pheromone_ma)
        
        self.operation_node_ids = self.enviroment.getOperationNodeIDs() # List of (j,k) tuples
        self.graph_edges = self.enviroment.getEdges() # List of actual edge tuples

    def releaseTheAnts(self):
        results_control = {}
        all_times_overall = [] # To store makespans from all ants across all cycles
        best_overall_time = float('inf')
        best_overall_path_nodes = []

        for cycle_number in range(self.cycles):
            this_cycle_times = []
            # Get the current graph (pheromones might have changed)
            current_graph_state = self.enviroment.getGraph() 
            
            # For accumulating pheromone contributions in this cycle
            this_cycle_contributions_js = {edge: 0.0 for edge in self.graph_edges}
            this_cycle_contributions_ma = {edge: 0.0 for edge in self.graph_edges}

            for ant_idx in range(self.ant_numbers):
                ant = Ant(current_graph_state, self.operation_node_ids, # Pass (j,k) op ids
                          self.ALPHA_JS, self.ALPHA_MA, self.BETA, 
                          self.seed, extended_seed=cycle_number * self.ant_numbers + ant_idx) # Unique seed per ant
                
                # ant_path_edges: sequence of ((u,v),(x,y)) tuples defining path
                # ant_path_nodes_sequence: sequence of (j,k) operations chosen by ant
                ant_path_edges, ant_path_nodes_sequence = ant.walk()
                
                if not ant_path_nodes_sequence : # Ant failed to find a complete path
                    # print(f"Warning: Ant {ant_idx} in cycle {cycle_number} did not produce a valid path.")
                    path_time = float('inf') # Penalize incomplete paths
                else:
                    path_time = self.enviroment.calculateMakespanTime(ant_path_nodes_sequence)

                this_cycle_times.append(path_time)
                all_times_overall.append(path_time)

                if path_time < best_overall_time:
                    best_overall_time = path_time
                    best_overall_path_nodes = ant_path_nodes_sequence
                
                # Pheromone contribution: only if path is valid (finite time)
                if path_time != float('inf') and path_time > 0 : # path_time > 0 for safety with division
                    for edge in ant_path_edges: # Edges are ((prev_op), (curr_op))
                        # Ensure edge exists in contributions dict (should if graph_edges is comprehensive)
                        if edge in this_cycle_contributions_js:
                             this_cycle_contributions_js[edge] += self.pheromone_constant_js / path_time
                             this_cycle_contributions_ma[edge] += self.pheromone_constant_ma / path_time
                        # else:
                            # This can happen if an ant traverses an edge not initially in self.graph_edges
                            # (e.g., if graph is dynamic or ant can create edges - not the case here).
                            # Or if self.graph_edges was not exhaustive from G.edges() initially.
                            # print(f"Warning: Edge {edge} from ant path not in contributions dict.")


            # Update pheromones on all edges in the graph
            self.enviroment.updatePheromone(
                self.evaporation_rate_js, self.evaporation_rate_ma,
                this_cycle_contributions_js, this_cycle_contributions_ma
            )

            # Save recorded values for this cycle
            if this_cycle_times: # Ensure list is not empty
                 results_control[cycle_number] = [
                    min(this_cycle_times) if any(t != float('inf') for t in this_cycle_times) else float('inf'), # Handle all inf
                    mean(t for t in this_cycle_times if t != float('inf')) if any(t != float('inf') for t in this_cycle_times) else float('inf'),
                    max(t for t in this_cycle_times if t != float('inf')) if any(t != float('inf') for t in this_cycle_times) else float('inf')
                ]
            else: # Should not happen if ant_numbers > 0
                results_control[cycle_number] = [float('inf'), float('inf'), float('inf')]
            
            print(f"Cycle {cycle_number+1}/{self.cycles} | Min: {results_control[cycle_number][0]:.2f}, Mean: {results_control[cycle_number][1]:.2f}, Max: {results_control[cycle_number][2]:.2f} | Overall Best: {best_overall_time:.2f}")


        # Generating file with fitness through cycles
        try:
            with open("ACO_cycles_results.json", 'w') as f:
                json.dump(results_control, f, indent=4)
        except Exception as e:
            print(f"Error saving results to JSON: {e}")

        # Print final results
        print("---------------------------------------------------")
        valid_overall_times = [t for t in all_times_overall if t != float('inf')]
        if valid_overall_times:
            print(f"Mean of all valid makespans: {mean(valid_overall_times):.2f}")
            if len(valid_overall_times) > 1:
                print(f"Standard deviation of valid makespans: {stdev(valid_overall_times):.2f}")
            else:
                print("Standard deviation: N/A (less than 2 valid times)")
            print(f"BEST OVERALL MAKESPAN: {best_overall_time:.2f}")
            # print(f"Best path (sequence of operations (job, op_idx)): {best_overall_path_nodes}")
        else:
            print("No valid solutions found across all cycles.")
        print("---------------------------------------------------")
        
        # Optionally print the graph at the end
        # self.enviroment.printGraph()
        
        return best_overall_time, best_overall_path_nodes