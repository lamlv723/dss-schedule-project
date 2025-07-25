from deap import base, creator

creator.create("FitnessMax", base.Fitness, weights=(1.0,))

# Create the Individual class. It will be a list of tuples, where each
# tuple is (task_id, start_time_slot). The individual now has the FitnessMax attribute.
creator.create("Individual", list, fitness=creator.FitnessMax)