# main.py
import random
import config
import utils
from fitness_function import get_fitness 

# ==========================================
# 1. 升级版遗传算子
# ==========================================

def crossover(parent1, parent2):
    """
    均匀交叉 (Uniform Crossover)
    """
    child1, child2 = [], []
    for i in range(len(parent1)):
        if random.random() < 0.5:
            child1.append(parent1[i])
            child2.append(parent2[i])
        else:
            child1.append(parent2[i])
            child2.append(parent1[i])
    return child1, child2

def mutate(melody, rate):
    """
    [关键修改] 混合变异算子：结合了“大幅重置”和“微调优化”
    """
    new_melody = melody[:]
    for i in range(len(new_melody)):
        if random.random() < rate: 
            prob = random.random()
            
            # 策略 A (30%概率): 剧烈变异 (重置为休止符或随机音)
            # 作用：探索全新的可能性，跳出当前思维定势
            if prob < 0.3:
                if random.random() < config.REST_PROB:
                    new_melody[i] = 0
                else:
                    new_melody[i] = random.randint(config.PITCH_MIN, config.PITCH_MAX)
            
            # 策略 B (70%概率): 微调变异 (上下移动 1-2 个半音)
            # 作用：在保留乐句形状的基础上进行“精修” (Local Search)
            else:
                if new_melody[i] != 0:
                    shift = random.choice([-2, -1, 1, 2])
                    val = new_melody[i] + shift
                    # 确保不越界
                    if config.PITCH_MIN <= val <= config.PITCH_MAX:
                        new_melody[i] = val
    return new_melody

# ==========================================
# 2. 训练主循环
# ==========================================

def train():
    # 强制覆盖配置中的代数，确保跑够 500 代
    TOTAL_GENS = 500 
    print(f"Start training... Target: {TOTAL_GENS} generations.")

    # 1. 初始化
    population = [utils.generate_random_melody() for _ in range(config.POPULATION_SIZE)]
    
    stagnation_counter = 0     
    last_best_score = -9999    
    current_mutation_rate = config.MUTATION_RATE_BASE

    for generation in range(TOTAL_GENS):
        # --- A. 评估 ---
        scored_population = [(get_fitness(ind), ind) for ind in population]
        # 按分数从高到低排序
        scored_population.sort(key=lambda x: x[0], reverse=True)
        
        best_score, best_melody = scored_population[0]
        
        # --- B. 监控与自适应 ---
        if best_score <= last_best_score + 0.01: # 加上0.01防止浮点数误差
            stagnation_counter += 1
        else:
            if stagnation_counter > 10:
                print(f"  >>> [进化突破] 分数提升至 {best_score:.2f} (停滞了 {stagnation_counter} 代)")
            stagnation_counter = 0
            current_mutation_rate = config.MUTATION_RATE_BASE # 恢复平静
            last_best_score = best_score
        
        # [机制1] 动态变异率
        if stagnation_counter > 20:
            current_mutation_rate = 0.15 # 适度提升焦虑感
        
        # [机制2] 大灭绝 (Cataclysm) - 专治长期早熟
        if stagnation_counter > 50:
            print(f"[触发灭绝] 长期停滞，清除 99% 的种群")
            # 只保留前 5 名精英，其他全部杀掉换成随机新个体
            survivors = [p[1] for p in scored_population[:5]]
            new_bloods = [utils.generate_random_melody() for _ in range(config.POPULATION_SIZE - 5)]
            population = survivors + new_bloods
            
            # 重置计数器
            stagnation_counter = 0
            current_mutation_rate = config.MUTATION_RATE_BASE
            print(f"  >>> 种群重建完成，新一轮进化开始。")
            continue # 跳过本轮剩下的繁殖步骤，直接进入下一代

        # 打印日志
        if generation % 10 == 0:
            print(f"Gen {generation}: Best={best_score:.2f} | Stag={stagnation_counter} | Mut={current_mutation_rate:.2f}")

        # --- C. 选择与繁殖 ---
        new_population = []
        
        # [策略1] 精英保留 (Unique Elitism) - 严格去重
        seen_hashes = set()
        for score, melody in scored_population:
            h = tuple(melody)
            if h not in seen_hashes:
                new_population.append(melody)
                seen_hashes.add(h)
            if len(new_population) >= config.ELITISM_COUNT:
                break
        
        # [机制3] 鲶鱼效应 (Immigration)
        # 强制在每一代引入 5% 的全新随机个体，防止基因池固化
        num_immigrants = int(config.POPULATION_SIZE * 0.05)
        for _ in range(num_immigrants):
            new_population.append(utils.generate_random_melody())

        # [策略2] 锦标赛繁殖
        while len(new_population) < config.POPULATION_SIZE:
            # 锦标赛大小 k=3，压力适中
            parents = random.sample(scored_population, 6) # 取6个做两次锦标赛
            # 父本1
            p1 = max(parents[:3], key=lambda x:x[0])[1]
            # 父本2
            p2 = max(parents[3:], key=lambda x:x[0])[1]
            
            c1, c2 = crossover(p1, p2)
            new_population.append(mutate(c1, current_mutation_rate))
            if len(new_population) < config.POPULATION_SIZE:
                new_population.append(mutate(c2, current_mutation_rate))
                
        population = new_population

    print("Training Complete.")
    return scored_population[0][1]

if __name__ == "__main__":
    final_melody = train()
    utils.save_melody_to_midi(final_melody, "final_composition_500gen.mid")