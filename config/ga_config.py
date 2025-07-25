# --- GA Parameters ---
POPULATION_SIZE = 100
CROSSOVER_PROBABILITY = 0.8
MUTATION_PROBABILITY = 0.3
N_GENERATIONS = 100

# --- Selection Parameters ---
# Number of individuals to compete in each tournament
TOURNAMENT_SIZE = 3

# --- Elitism Parameters ---
# Percentage of the best individuals to carry over to the next generation
ELITE_SIZE_PERCENT = 0.1
ELITE_SIZE = int(POPULATION_SIZE * ELITE_SIZE_PERCENT)

# --- Mutation Parameters ---
# Probability for each type of mutation
# The sum should ideally be 1.0
MUTATION_TYPE_PROBS = {
    "reschedule": 0.5,
    "swap": 0.3,
    "creep": 0.2
}

# --- Fitness Function Weights ---
# These weights determine the importance of each soft constraint.
# Higher values mean the GA will prioritize satisfying that constraint.
FITNESS_WEIGHTS = {
    "priority": 0.3,
    "deadline": 0.4,
    "idle_time": 0.2,
    "category_switching": 0.1,
}

# --- Fitness Score Scaling ---
MAX_FITNESS_SCORE = 100000