# ga_core/engine.py

import random
import numpy as np
from deap import base, tools, creator
from config import ga_config
from ga_core import operators, fitness, chromosome

def run_ga_optimization(tasks_map, task_instances, blocked_slots, progress_callback):
    """
    Sets up and runs the genetic algorithm.
    """
    toolbox = base.Toolbox()

    toolbox.register("individual", operators.create_random_schedule, creator.Individual, 
                     task_instances=task_instances, blocked_slots=blocked_slots)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    toolbox.register("evaluate", fitness.calculate_fitness, tasks_map=tasks_map, blocked_slots=blocked_slots)
    toolbox.register("mate", operators.custom_crossover, task_instances=task_instances)
    toolbox.register("mutate", operators.custom_mutation, blocked_slots=blocked_slots)
    toolbox.register("select", tools.selTournament, tournsize=ga_config.TOURNAMENT_SIZE)

    population = toolbox.population(n=ga_config.POPULATION_SIZE)
    
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean)
    stats.register("min", np.min)
    stats.register("max", np.max)
    
    logbook = tools.Logbook()
    logbook.header = "gen", "avg", "min", "max"

    fitnesses = map(toolbox.evaluate, population)
    for ind, fit in zip(population, fitnesses):
        ind.fitness.values = fit

    for gen in range(ga_config.N_GENERATIONS):
        elites = tools.selBest(population, k=ga_config.ELITE_SIZE)
        elites = [toolbox.clone(el) for el in elites]

        offspring = toolbox.select(population, len(population) - ga_config.ELITE_SIZE)
        offspring = [toolbox.clone(ind) for ind in offspring]

        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < ga_config.CROSSOVER_PROBABILITY:
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values

        for mutant in offspring:
            if random.random() < ga_config.MUTATION_PROBABILITY:
                toolbox.mutate(mutant)
                del mutant.fitness.values

        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        new_fitnesses = map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, new_fitnesses):
            ind.fitness.values = fit

        population[:] = elites + offspring
        
        record = stats.compile(population)
        logbook.record(gen=gen + 1, **record)
        
        progress_value = (gen + 1) / ga_config.N_GENERATIONS

        best_score = record.get('max', 0.0)
        progress_callback(progress_value, f"Generation {gen + 1}/{ga_config.N_GENERATIONS} - Best Score: {best_score:.4f}")

    best_individual = tools.selBest(population, k=1)
    
    return best_individual, logbook