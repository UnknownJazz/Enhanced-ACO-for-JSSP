from aco import ACO

# Set parameters for model:
parameters = {
    "seed" : 0, # Random seed
    
    "ALPHA_JS" : 1.0, # Influence of Job Sequencing Pheromone
    "ALPHA_MA" : 1.0, # Influence of Machine Affinity Pheromone
    "BETA" : 2.0,     # Influence of heuristic desirability
    
    "init_pheromone_js" : 0.1, # Initial JS Pheromone
    "init_pheromone_ma" : 0.1, # Initial MA Pheromone
    
    "pheromone_constant_js" : 1.0, # Pheromone update constant for JS
    "pheromone_constant_ma" : 1.0, # Pheromone update constant for MA
    
    "min_pheromone_js" : 0.001, # Minimum JS Pheromone
    "min_pheromone_ma" : 0.001, # Minimum MA Pheromone
    
    "evaporation_rate_js" : 0.1, # Evaporation rate for JS Pheromone (1 - rho_js)
    "evaporation_rate_ma" : 0.1, # Evaporation rate for MA Pheromone (1 - rho_ma)
    # Note: evaporation_rate is typically rho (persistence). If it's (1-rho), then values like 0.1 (strong evaporation) are common.
    # The original code used 0.91, implying persistence factor. Let's stick to that interpretation:
    # "evaporation_rate" is how much remains. So, if 0.1 evaporates, 0.9 remains.
    # If the parameter means "rate of evaporation", then 0.1 is typical. If it means "persistence factor rho", then 0.9 is typical.
    # The original code was (evaporation_rate * old_pheromone), so it's persistence.
    # Let's assume persistence for these too.
    "evaporation_persistence_js" : 0.9, # Persistence factor for JS (rho_js)
    "evaporation_persistence_ma" : 0.9, # Persistence factor for MA (rho_ma)

    "ant_numbers" : 20, # Number of ants per cycle
    "cycles" : 50,    # Number of cycles (iterations)
    
    "dataset" : 'ft06.txt' # File name for JSSP instance
    # Ensure 'ft06.txt', 'la01.txt' etc. are in a folder named 'test_instances' 
    # in the parent directory of where your script runs.
    # E.g., if script is in 'project/code/main.py', instances should be in 'project/test_instances/ft06.txt'
}

# Test with a smaller dataset first if needed, e.g., ft06.txt
# parameters["dataset"] = 'ft06.txt' 
# parameters["cycles"] = 20
# parameters["ant_numbers"] = 10


colony = ACO(
    ALPHA_JS=parameters['ALPHA_JS'],  
    ALPHA_MA=parameters['ALPHA_MA'],
    BETA=parameters['BETA'],
    dataset=parameters['dataset'],
    cycles=parameters['cycles'],
    ant_numbers=parameters['ant_numbers'],
    init_pheromone_js=parameters['init_pheromone_js'],
    init_pheromone_ma=parameters['init_pheromone_ma'],
    pheromone_constant_js=parameters['pheromone_constant_js'],
    pheromone_constant_ma=parameters['pheromone_constant_ma'],
    min_pheromone_js=parameters['min_pheromone_js'],
    min_pheromone_ma=parameters['min_pheromone_ma'],
    evaporation_rate_js=parameters['evaporation_persistence_js'], # Using persistence factor
    evaporation_rate_ma=parameters['evaporation_persistence_ma'], # Using persistence factor
    seed=parameters['seed']
)

best_time, best_path = colony.releaseTheAnts()
# print(f"\nFinal Best Makespan: {best_time}")
# print(f"Final Best Path (Operation Sequence): {best_path}")

# You might want to visualize the graph after execution, uncomment in ACO.py if needed
# colony.enviroment.printGraph()