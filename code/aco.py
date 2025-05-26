from enviroment import Enviroment
from ant import Ant
import copy
from statistics import mean, stdev
import json
import numpy as np


class ACO():
    """
    Class responsible to manage the
    entire proccess. 
    It creates and executes the graph enviroment
    all the ants, updates the pheromones and 
    at the registers the best solution found.

    returns:
        Best Makespam time of critical path.
        Sequence Job/Machine for this path.
    """ 

    def __init__(self, ALPHA, BETA, dataset, cycles, ant_numbers, init_pheromone, pheromone_constant, min_pheromone, evaporation_rate, seed):
        self.ALPHA = ALPHA
        self.ant_numbers = ant_numbers
        self.BETA = BETA
        self.cycles = cycles
        self.pheromone_constant = pheromone_constant
        self.evaporation_rate = evaporation_rate
        self.seed = seed

        #Inicialize the Enviroment and set data
        self.enviroment = Enviroment(dataset, init_pheromone, min_pheromone)
        self.time_of_executions = self.enviroment.getTimeOfExecutions()
        self.node_names = self.enviroment.getNodeNames()
        self.graph_edges = self.enviroment.getEdges()
    

    def releaseTheAnts(self):
        results_control = {}
        all_times = []
        best_path = None
        best_time = float('inf')

        for cycle_number in range(self.cycles):
            this_cycle_times = []
            this_cycle_Graph = self.enviroment.getGraph()
            this_cycle_edges_contributions = dict.fromkeys(self.graph_edges, 0)

            for ant_number in range(self.ant_numbers):
                ant = Ant(this_cycle_Graph, self.node_names, self.ALPHA, self.BETA, self.seed, ant_number)
                ant_path = ant.walk()
                path_time = self.enviroment.calculateMakespanTime(ant_path)

                for edge in ant_path:
                    this_cycle_edges_contributions[edge] += self.pheromone_constant / path_time

                this_cycle_times.append(path_time)
                all_times.append(path_time)

                # Track the best path
                if path_time < best_time:
                    best_time = path_time
                    best_path = ant_path

            # Global pheromone update
            self.enviroment.updatePheromone(self.evaporation_rate, this_cycle_edges_contributions)

            # Elitist update: reinforce the best path
            if best_path:
                elite_contribution = dict.fromkeys(self.graph_edges, 0)
                for edge in best_path:
                    elite_contribution[edge] += self.pheromone_constant / best_time
                self.enviroment.updatePheromone(1.0, elite_contribution)  # No evaporation for elitist update

            results_control[cycle_number] = [min(this_cycle_times), mean(this_cycle_times), max(this_cycle_times)]

        json.dump(results_control, open("ACO_cycles_results.json", 'w'))
        print("---------------------------------------------------")
        print("Mean: ", mean(all_times))
        print("Standard deviation: ", stdev(all_times))
        print("BEST PATH TIME: ", best_time, " seconds")
        print("---------------------------------------------------")
 