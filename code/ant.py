import numpy as np

class Ant():
    def __init__(self, Graph, operation_node_ids, ALPHA_JS, ALPHA_MA, BETA, seed, extended_seed): # Changed node_names to operation_node_ids
        self.seed = seed + extended_seed
        self.ALPHA_JS = ALPHA_JS
        self.ALPHA_MA = ALPHA_MA
        self.BETA = BETA
        self.G = Graph  
        self.operation_node_ids = operation_node_ids # These are (j,k) tuples for operations
        self.not_visited_ops = self.operation_node_ids.copy() # List of (j,k) op_ids
        self.ant_path_edges = [] # Stores sequence of edges ((prev_op), (curr_op))
        self.ant_path_nodes = [] # Stores sequence of operations (nodes) (curr_op)

    def walk(self):
        """
        The ant walks on every operation node of the graph once.
        The path generated is a permutation of all operations.
        Returns:
            List of edges followed: [((u1,v1),(u2,v2)), ((u2,v2),(u3,v3)), ...]
            Path of nodes (operations) visited in order: [(u2,v2), (u3,v3), ...]
        """
        np.random.seed(self.seed)
        current_op_node = (-1, -1) # Start on initial virtual node
        self.ant_path_nodes.append(current_op_node) # Virtual start node is part of the conceptual path start

        while self.not_visited_ops: # While there are operations to schedule
            if len(self.not_visited_ops) == 1:
                next_op_node = self.not_visited_ops[0]
            else:
                # __chooseNextNode now takes the list of available choices (self.not_visited_ops)
                next_op_node = self.__chooseNextNode(current_op_node, self.not_visited_ops)
            
            self.ant_path_edges.append((current_op_node, next_op_node))
            self.ant_path_nodes.append(next_op_node) # Add chosen op to node path
            
            current_op_node = next_op_node
            try:
                self.not_visited_ops.remove(next_op_node)
            except ValueError:
                # This can happen if next_op_node was somehow not in not_visited_ops
                # Or if __chooseNextNode returns something not from the provided list.
                # This shouldn't occur with correct logic.
                print(f"Error: Tried to remove {next_op_node} which was not in not_visited_ops.")
                print(f"Current not_visited_ops: {self.not_visited_ops[:5]}...") # Print some for debugging
                break # Avoid infinite loop

        # The makespan calculation needs only the sequence of actual operations, not the virtual start or edges.
        actual_op_sequence = [node for node in self.ant_path_nodes if node != (-1,-1)]
        return self.ant_path_edges, actual_op_sequence


    def __chooseNextNode(self, current_op_node, available_ops_to_choose_from):
        """
        Chooses the next operation node to visit from the 'available_ops_to_choose_from' list.
        """
        node_probabilities = self.__calculateNodeProbabilityChoices(current_op_node, available_ops_to_choose_from)
        
        if not node_probabilities: # Should not happen if available_ops_to_choose_from is not empty
            # Fallback: if probabilities are all zero or list is empty, pick randomly if possible
            if available_ops_to_choose_from:
                return np.random.choice(available_ops_to_choose_from)
            else: # This case should be prevented by the calling logic in walk()
                raise ValueError("Cannot choose next node: no available operations or probabilities.")

        nodes = list(node_probabilities.keys())  
        probabilities_values = list(node_probabilities.values())
        
        # Normalize probabilities (important: numpy.random.choice requires sum to be 1)
        # Sum can be zero if all pheromones/desirabilities led to zero partial_prob
        prob_sum = sum(probabilities_values)
        if prob_sum == 0:
            # All choices have zero probability, implies an issue or all pheromones are at min and desirability is 0
            # Fallback: uniform random choice among available nodes
            normalized_probabilities = [1.0 / len(nodes)] * len(nodes) if nodes else []
        else:
            normalized_probabilities = [p / prob_sum for p in probabilities_values]

        # Ensure normalization due to potential floating point inaccuracies
        if normalized_probabilities and sum(normalized_probabilities) != 1.0:
             diff = 1.0 - sum(normalized_probabilities)
             normalized_probabilities[-1] += diff # Adjust last element

        if not nodes: # Should be caught earlier
            raise ValueError("Cannot choose next node: node list from probabilities is empty.")
            
        try:
            chosen_idx = np.random.choice(len(nodes), p=normalized_probabilities)
            return nodes[chosen_idx]
        except ValueError as e:
            # print(f"Error in np.random.choice: {e}")
            # print(f"Nodes: {nodes}")
            # print(f"Probabilities: {normalized_probabilities}, Sum: {sum(normalized_probabilities)}")
            # Fallback if choice fails (e.g. due to extreme probability values or all zeros after normalization attempt)
            return np.random.choice(nodes) if nodes else None # Should not be None if available_ops is checked

    def __calculateNodeProbabilityChoices(self, current_op_node, available_ops):
        """
        Calculates the probability for choosing each operation in 'available_ops'
        when transitioning from 'current_op_node'.
        Returns: Dict {op_node: probability_value}
        """
        node_partial_probabilities = {}
        total_partial_probability = 0

        for next_op_candidate in available_ops:
            if not self.G.has_edge(current_op_node, next_op_candidate):
                # This case should ideally not happen if the graph is fully connected as intended
                # (virtual start to all ops, all ops to all other ops)
                # print(f"Warning: No edge from {current_op_node} to {next_op_candidate}")
                # Assign a very small probability or skip
                partial_prob = 1e-9 # A tiny non-zero value to allow selection if all others are also missing
            else:
                edge_data = self.G[current_op_node][next_op_candidate]
                pheromone_js = edge_data['pheromone_js']
                pheromone_ma = edge_data['pheromone_ma']
                desirability = edge_data['desirability']
                
                # ACO formula for choice
                partial_prob = (pheromone_js ** self.ALPHA_JS) * \
                               (pheromone_ma ** self.ALPHA_MA) * \
                               (desirability ** self.BETA)
            
            node_partial_probabilities[next_op_candidate] = partial_prob
            total_partial_probability += partial_prob
        
        # Normalize to get actual probabilities (though __chooseNextNode does further normalization)
        # This dict returned is more like weighted scores before final normalization in __chooseNextNode
        # if total_partial_probability == 0: # All partials are zero
        #     # Return uniform scores if all are zero, or let __chooseNextNode handle it
        #     if available_ops:
        #         return {node: 1.0/len(available_ops) for node in available_ops}
        #     else:
        #         return {}
        
        # The __chooseNextNode will handle normalization of these partial_probabilities.
        return node_partial_probabilities