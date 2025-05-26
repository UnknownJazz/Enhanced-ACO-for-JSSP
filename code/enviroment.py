import networkx as nx
import matplotlib
import matplotlib.pyplot as plt

class Enviroment():

    def __init__(self, file_name, init_pheromone_js, init_pheromone_ma, min_pheromone_js, min_pheromone_ma):
        self.min_pheromone_js = min_pheromone_js
        self.min_pheromone_ma = min_pheromone_ma
        
        # Read and parse data into a more structured format for operations
        self.operations_data, self.num_jobs, self.num_total_machines = self.__readAndParseData(file_name)
        
        # Create Graph
        # self.node_op_ids will be a list of (job_idx, op_idx_in_job) tuples
        self.G, self.node_op_ids = self.__buildGraph(init_pheromone_js, init_pheromone_ma)


    def __readAndParseData(self, file_name):
        """
        Reads file and creates a structured representation of operations.
        Each operation is (job_idx, op_idx_in_job) -> {'machine': m, 'time': t}.

        returns:
            operations_data: List of lists. operations_data[job_idx][op_idx_in_job] = {'machine': m, 'time': t}
            num_jobs: Total number of jobs.
            num_total_machines: Highest machine index encountered + 1.
        """
        jobs_operations_list = []
        max_machine_id = -1
        
        try:
            with open("../test_instances/" + file_name, 'r') as file:
                job_idx = 0
                for line in file:
                    if not line.strip(): continue # Skip empty lines
                    
                    parts = line.split()
                    current_job_ops = []
                    op_idx_in_job = 0
                    for i in range(0, len(parts), 2):
                        machine = int(parts[i])
                        time = int(parts[i+1])
                        current_job_ops.append({'machine': machine, 'time': time, 'original_job_idx': job_idx, 'op_idx_in_job': op_idx_in_job})
                        if machine > max_machine_id:
                            max_machine_id = machine
                        op_idx_in_job +=1
                    jobs_operations_list.append(current_job_ops)
                    job_idx +=1
        except FileNotFoundError:
            print(f"Error: File not found at ../test_instances/{file_name}")
            print("Please ensure the 'test_instances' folder is in the parent directory of your script's location,")
            print("or adjust the path in Enviroment.__readAndParseData.")
            raise

        num_jobs = len(jobs_operations_list)
        num_total_machines = max_machine_id + 1
        
        return jobs_operations_list, num_jobs, num_total_machines

    def __buildGraph(self, init_pheromone_js, init_pheromone_ma):
        """
        Creates a Directed Graph. Nodes are operations (job_idx, op_idx_in_job).
        Includes a virtual start node (-1,-1).
        Edges store 'pheromone_js', 'pheromone_ma', and 'desirability'.
        """
        all_op_ids = []
        for j_idx, job_ops in enumerate(self.operations_data):
            for o_idx in range(len(job_ops)):
                all_op_ids.append((j_idx, o_idx))

        # Create graph with operation nodes and the virtual start node
        graph_nodes = [(-1,-1)] + all_op_ids
        G = nx.DiGraph()
        G.add_nodes_from(graph_nodes)

        # Add edges and their attributes
        virtual_start_node = (-1,-1)
        for op_id_to in all_op_ids: # Edges from virtual start node
            j_to, o_to = op_id_to
            time_to = self.operations_data[j_to][o_to]['time']
            desirability = 1.0 / time_to if time_to > 0 else float('inf') # Avoid division by zero

            G.add_edge(virtual_start_node, op_id_to,
                       pheromone_js=init_pheromone_js,
                       pheromone_ma=init_pheromone_ma,
                       desirability=desirability)

        for op_id_from in all_op_ids: # Edges between operation nodes
            j_from, o_from = op_id_from
            for op_id_to in all_op_ids:
                if op_id_from == op_id_to:
                    continue # No self-loops
                
                j_to, o_to = op_id_to
                time_to = self.operations_data[j_to][o_to]['time']
                desirability = 1.0 / time_to if time_to > 0 else float('inf')

                G.add_edge(op_id_from, op_id_to,
                           pheromone_js=init_pheromone_js,
                           pheromone_ma=init_pheromone_ma,
                           desirability=desirability)
        
        # self.node_op_ids are the actual operation identifiers for ants to visit
        return G, all_op_ids


    def getGraph(self):
        return self.G
    
    def getOperationNodeIDs(self): # Changed from getNodeNames
        return self.node_op_ids

    def getOperationsData(self): # To provide machine/time info
        return self.operations_data

    def getEdges(self):
        return list(self.G.edges)

    def updatePheromone(self, evaporation_rate_js, evaporation_rate_ma,
                        cycle_edge_contributions_js, cycle_edge_contributions_ma):
        """
        Updates both pheromone trails on all edges.
        """
        for edge in self.G.edges:
            from_node, to_node = edge
            
            # Update JS Pheromone
            old_pheromone_js = self.G[from_node][to_node]['pheromone_js']
            new_pheromone_js = cycle_edge_contributions_js.get(edge, 0) + (evaporation_rate_js * old_pheromone_js)
            self.G[from_node][to_node]['pheromone_js'] = max(new_pheromone_js, self.min_pheromone_js)
            
            # Update MA Pheromone
            old_pheromone_ma = self.G[from_node][to_node]['pheromone_ma']
            new_pheromone_ma = cycle_edge_contributions_ma.get(edge, 0) + (evaporation_rate_ma * old_pheromone_ma)
            self.G[from_node][to_node]['pheromone_ma'] = max(new_pheromone_ma, self.min_pheromone_ma)


    def calculateMakespanTime(self, path_of_op_ids_as_priority):
        """
        Calculates makespan for a given permutation of operations (path_of_op_ids_as_priority).
        This permutation serves as a priority list for an active schedule generator.
        """
        num_total_ops = len(self.node_op_ids) # Total number of unique operations (j,k)
        
        op_actual_finish_time = {} # Stores finish_time for each (j,k) op_id once scheduled
        machine_available_at = [0] * self.num_total_machines

        S_completed = set()
        all_ops_set = set(self.node_op_ids) # All (j,k) operations

        while len(S_completed) < num_total_ops:
            S_candidate = set() # Operations whose predecessors are completed
            for op_jk in all_ops_set - S_completed:
                j, k = op_jk
                if k == 0: # First operation of this job
                    S_candidate.add(op_jk)
                else:
                    pred_op = (j, k - 1)
                    if pred_op in S_completed: # Predecessor is done
                        S_candidate.add(op_jk)
            
            if not S_candidate:
                if len(S_completed) < num_total_ops:
                    # This implies a deadlock or an issue, should not happen in a valid JSSP if all ops are schedulable
                    # Or simply all remaining operations are waiting for machine availability or precedence.
                    # This scheduling logic might need to advance time if no op can be chosen from path.
                    # For now, assume an op will always be chosen if candidates exist.
                    # print(f"Warning: No candidate operations to schedule, but {num_total_ops - len(S_completed)} ops remaining.")
                    return float('inf') # Error or invalid schedule state
                break # All operations scheduled

            # Determine earliest start time (EST) for each candidate operation
            op_est_map = {}
            for op_jk in S_candidate:
                j, k = op_jk
                op_details = self.operations_data[j][k]
                machine = op_details['machine']
                
                pred_finish_time_for_job = 0
                if k > 0:
                    pred_op = (j, k - 1)
                    pred_finish_time_for_job = op_actual_finish_time[pred_op]
                
                current_op_est = max(pred_finish_time_for_job, machine_available_at[machine])
                op_est_map[op_jk] = current_op_est
                
            # Select operation from S_candidate using the ant's path as a priority list.
            # Pick the operation in S_candidate that appears earliest in path_of_op_ids_as_priority.
            chosen_op_to_schedule = None
            for op_from_path in path_of_op_ids_as_priority: # Iterate through the ant's prioritized list
                if op_from_path in S_candidate and op_from_path not in S_completed:
                    chosen_op_to_schedule = op_from_path
                    break 
            
            if chosen_op_to_schedule is None:
                 # All ops in S_candidate might have already been processed from the path, or path is misformed.
                 # Or, if S_candidate is not empty, but no op from S_candidate is found by iterating ant's path (if ant's path is exhausted prematurely)
                 # This implies a potential issue if S_candidate is not empty.
                 # A robust way is to pick from S_candidate based on some rule if ant's path doesn't guide, e.g., min EST.
                 # For now, if ant's path cannot select, it's problematic.
                if S_candidate: # If there are candidates but ant path didn't pick one (e.g. path exhausted or only contains completed ops)
                    # Fallback: pick one with min EST, tie-break with path order if possible or arbitrarily
                    chosen_op_to_schedule = min(S_candidate, key=lambda op: (op_est_map[op], path_of_op_ids_as_priority.index(op) if op in path_of_op_ids_as_priority else float('inf')))

                if chosen_op_to_schedule is None and S_candidate : # Still none, pick any
                     chosen_op_to_schedule = list(S_candidate)[0]


            if chosen_op_to_schedule is None : # if S_candidate was empty and we broke, or still couldn't pick
                 if len(S_completed) < num_total_ops:
                    # print("Error in makespan: Could not select an operation to schedule.")
                    return float('inf') # Should not happen if S_candidate was non-empty
                 else: # All ops scheduled
                    break


            j_chosen, k_chosen = chosen_op_to_schedule
            chosen_op_details = self.operations_data[j_chosen][k_chosen]
            machine_chosen = chosen_op_details['machine']
            duration_chosen = chosen_op_details['time']
            
            start_time = op_est_map[chosen_op_to_schedule]
            finish_time = start_time + duration_chosen
            
            op_actual_finish_time[chosen_op_to_schedule] = finish_time
            machine_available_at[machine_chosen] = finish_time # Update machine availability
            S_completed.add(chosen_op_to_schedule)

        makespan = 0
        if op_actual_finish_time:
            makespan = max(op_actual_finish_time.values())
        else: # No operations were scheduled
            return 0 if num_total_ops == 0 else float('inf') # Makespan is 0 if no ops, else error

        return makespan


    def printGraph(self):
        """
        Creates an image of the built graph.
        Edge labels show (desirability, pheromone_js, pheromone_ma).
        """
        if not self.G or not self.G.nodes:
            print("Graph is empty, cannot print.")
            return

        options = {
            'node_color': 'lightblue',
            'node_size': 1000,
            'width': 1.5,
            'arrowstyle': '-|>',
            'arrowsize': 15,
            'font_size': 6,
            'with_labels': True
        }
        matplotlib.use('Agg') # Non-interactive backend
        
        edge_labels = {}
        for from_node, to_node, edge_data in self.G.edges(data=True):
            des = round(edge_data.get('desirability', 0), 3)
            ph_js = round(edge_data.get('pheromone_js', 0), 3)
            ph_ma = round(edge_data.get('pheromone_ma', 0), 3)
            # weight = f"D:{des}\nJS:{ph_js}\nMA:{ph_ma}" # Multi-line
            weight = f"({des}, {ph_js}, {ph_ma})" # Single line
            edge_labels[(from_node, to_node)] = weight

        fig = plt.figure(figsize=(16, 12))
        ax = fig.add_subplot(111)
        
        try:
            pos = nx.spring_layout(self.G, k=0.5, iterations=20, seed=42) # k adjusts spacing
        except Exception as e:
            print(f"Could not generate spring_layout, using random: {e}")
            pos = nx.random_layout(self.G, seed=42)

        nx.draw_networkx_nodes(self.G, pos, ax=ax, node_size=options['node_size'], node_color=options['node_color'])
        nx.draw_networkx_labels(self.G, pos, ax=ax, font_size=options['font_size']-1) # Smaller font for labels inside nodes
        nx.draw_networkx_edges(self.G, pos, ax=ax, arrowstyle=options['arrowstyle'], arrowsize=options['arrowsize'], width=options['width'], connectionstyle='arc3,rad=0.1')
        nx.draw_networkx_edge_labels(self.G, pos, edge_labels=edge_labels, font_size=options['font_size']-2, ax=ax) # Smaller font for edge labels
        
        plt.title("ACO Graph for JSSP Operations")
        plt.tight_layout()
        fig.savefig('graph.png')
        plt.close(fig)
        print("Graph image saved to graph.png")