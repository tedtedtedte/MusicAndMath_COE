# main.py
import random
import config
import utils
from fitness_function import get_fitness 

# --- 1. 改进的遗传算子 ---

def crossover(parent1, parent2):
    """
    均匀交叉 (Uniform Crossover)
    相比单点交叉，能更好地混合两个父代的优良基因片段，
    防止长序列（64步）的首尾基因难以组合的问题。
    """
    child1, child2 = [], []
    for i in range(len(parent1)):
        # 50% 概率取父本1，50% 取父本2
        if random.random() < 0.5:
            child1.append(parent1[i])
            child2.append(parent2[i])
        else:
            child1.append(parent2[i])
            child2.append(parent1[i])
    return child1, child2

def mutate(melody, rate):
    """
    变异算子
    """
    new_melody = melody[:]
    for i in range(len(new_melody)):
        if random.random() < rate: 
            # 变异逻辑：重置为休止符 或 随机音高
            if random.random() < config.REST_PROB:
                new_melody[i] = 0
            else:
                new_melody[i] = random.randint(config.PITCH_MIN, config.PITCH_MAX)
    return new_melody

# --- 2. 主训练循环 ---

def train():
    # 初始化种群
    population = [utils.generate_random_melody() for _ in range(config.POPULATION_SIZE)]
    print(f"Start training with population: {config.POPULATION_SIZE}")

    stagnation_counter = 0     # 停滞计数器
    last_best_score = -9999    # 上一代最高分
    current_mutation_rate = config.MUTATION_RATE_BASE

    for generation in range(config.GENERATIONS):
        # --- A. 评估与排序 ---
        # 计算所有个体的适应度
        scored_population = [(get_fitness(ind), ind) for ind in population]
        # 按分数从高到低排序
        scored_population.sort(key=lambda x: x[0], reverse=True)
        
        best_score, best_melody = scored_population[0]
        
        # --- B. 自适应监控 (避免局部最优) ---
        if best_score <= last_best_score:
            stagnation_counter += 1
        else:
            # 如果分数上涨，重置计数器和变异率
            if stagnation_counter > 5:
                print(f"  >>> 突破瓶颈！分数上升至 {best_score:.2f}")
            stagnation_counter = 0
            current_mutation_rate = config.MUTATION_RATE_BASE
            last_best_score = best_score
            
        # 动态调整变异率 (温和策略，避免破坏性重置)
        if stagnation_counter > 20:
            current_mutation_rate = 0.2   # 提高变异率，引入新基因
            if generation % 10 == 0: 
                print(f"  [警告] 长期停滞，提升变异率至 0.2")
        elif stagnation_counter > 10:
            current_mutation_rate = 0.1   # 轻微提升
        
        # 打印日志
        if generation % 10 == 0:
            print(f"Gen {generation}: Best Score={best_score:.2f} (MutRate={current_mutation_rate:.2f})")

        # --- C. 选择与繁殖 (核心修改) ---
        new_population = []
        
        # 1. 【去重精英保留】 (Unique Elitism)
        # 防止前50名全是同一个旋律的克隆体，导致死循环
        seen_melodies = set()
        unique_elites_count = 0
        
        for score, melody in scored_population:
            # 将列表转为tuple以便存入set比较
            melody_tuple = tuple(melody)
            if melody_tuple not in seen_melodies:
                new_population.append(melody) # 保留该精英
                seen_melodies.add(melody_tuple)
                unique_elites_count += 1
            
            if unique_elites_count >= config.ELITISM_COUNT:
                break
        
        # 如果去重后凑不够精英数量，用随机新个体补齐 (引入鲶鱼)
        while len(new_population) < config.ELITISM_COUNT:
            new_population.append(utils.generate_random_melody())
            
        # 2. 【繁殖】 (降低选择压力)
        while len(new_population) < config.POPULATION_SIZE:
            # 锦标赛选择：将 k 从 5 降为 3
            # 给“第二梯队”的潜力股更多机会
            batch1 = random.sample(scored_population, 2)
            p1 = max(batch1, key=lambda x:x[0])[1]
            
            batch2 = random.sample(scored_population, 2)
            p2 = max(batch2, key=lambda x:x[0])[1]
            
            # 交叉 & 变异
            c1, c2 = crossover(p1, p2)
            new_population.append(mutate(c1, current_mutation_rate))
            if len(new_population) < config.POPULATION_SIZE:
                new_population.append(mutate(c2, current_mutation_rate))
                
        # 更新种群
        population = new_population

    print("Training Complete.")
    return scored_population[0][1]

if __name__ == "__main__":
    final_melody = train()
    # 保存结果
    utils.save_melody_to_midi(final_melody, "final_composition.mid")