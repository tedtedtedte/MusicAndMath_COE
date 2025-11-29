# fitness_function.py

# ==========================================
# 1. 基础乐理常数与定义
# ==========================================

SCALE_C_MAJOR = {0, 2, 4, 5, 7, 9, 11} 
MIN_PITCH = 60
MAX_PITCH = 84

# 和弦定义 (I - V - vi - IV)
CHORD_C  = {0, 4, 7}   
CHORD_G  = {7, 11, 2}  
CHORD_Am = {9, 0, 4}   
CHORD_F  = {5, 9, 0}   

def get_chord_set(step_index):
    """根据时间步返回对应的和弦集合"""
    bar = step_index // 16 
    if bar == 0: return CHORD_C
    elif bar == 1: return CHORD_G
    elif bar == 2: return CHORD_Am
    elif bar == 3: return CHORD_F
    return CHORD_C 

# ==========================================
# 2. 基础规则 (正确性)
# ==========================================

def fitness_chords(melody):
    """和弦贴合度"""
    score = 0
    for i, note in enumerate(melody):
        if note == 0: continue
        target_chord = get_chord_set(i)
        note_class = note % 12
        is_strong_beat = (i % 4 == 0)
        
        if is_strong_beat:
            if note_class in target_chord: score += 10
            elif note_class in SCALE_C_MAJOR: score += 2
            else: score -= 10
        else:
            if note_class in SCALE_C_MAJOR: score += 6
            else: score -= 5
    return score

def fitness_intervals(melody):
    """音程流畅度：防止为了凑和弦而瞎跳"""
    score = 0
    pitches = [n for n in melody if n != 0]
    if len(pitches) < 2: return 0
    
    for i in range(len(pitches) - 1):
        interval = abs(pitches[i] - pitches[i+1])
        if interval <= 2: score += 5
        elif interval <= 4: score += 3
        elif interval > 7: score -= 5
        elif interval > 12: score -= 20
    return score

def fitness_variety(melody):
    """多样性：防止死板重复"""
    score = 0
    repeat_count = 0
    for i in range(1, len(melody)):
        if melody[i] == melody[i-1] and melody[i] != 0:
            repeat_count += 1
        else:
            repeat_count = 0
        if repeat_count > 3: score -= 5
    return score

# ==========================================
# 3. 进阶乐感规则 (由浅入深)
# ==========================================

def fitness_cadence(melody):
    """终止感：结尾要有回家的感觉"""
    if not melody: return 0
    last_note = melody[-1]
    if last_note == 0: return -10
    if last_note % 12 == 0: return 20 
    elif last_note % 12 in {4, 7}: return 5
    else: return -10

def fitness_gap_fill(melody):
    """大跳反向补偿：大跳之后必须反向，物理学定律"""
    score = 0
    pitches = [n for n in melody if n != 0]
    if len(pitches) < 3: return 0
    
    for i in range(len(pitches) - 2):
        d1 = pitches[i+1] - pitches[i]
        # 如果跳跃大于 5 个半音
        if abs(d1) > 5:
            d2 = pitches[i+2] - pitches[i+1]
            # 必须反向 或 保持不动
            if d1 * d2 < 0 or d2 == 0: score += 10 # 奖励提高，强制执行
            else: score -= 10
    return score

def fitness_melodic_inertia(melody):
    """
    (新增) 旋律惯性：保证线条的方向感。
    解决“微小跳跃感”的核心函数。
    """
    score = 0
    pitches = [n for n in melody if n != 0]
    if len(pitches) < 3: return 0

    for i in range(len(pitches) - 2):
        d1 = pitches[i+1] - pitches[i]
        d2 = pitches[i+2] - pitches[i+1]
        
        # 我们只关注小幅度的音程 (4个半音以内)
        # 因为大幅度跳跃已经由 gap_fill 接管了
        if abs(d1) <= 4 and abs(d2) <= 4:
            # 1. 奖励同向行进 (顺滑线条)
            # 例如：C -> D -> E (上行接上行)
            if d1 * d2 > 0: 
                score += 10 
            
            # 2. 惩罚小幅度的反向折返 (锯齿感)
            # 例如：C -> D -> C (无意义的抖动)
            elif d1 * d2 < 0:
                score -= 4

    return score

def fitness_range(melody):
    """音域控制"""
    score = 0
    out_of_range = 0
    for note in melody:
        if note == 0: continue
        if note < MIN_PITCH or note > MAX_PITCH:
            out_of_range += 1
    if out_of_range > 0: score -= (out_of_range * 2)
    return score

def fitness_rhythm_density(melody):
    """节奏呼吸"""
    note_count = sum(1 for n in melody if n != 0)
    total_len = len(melody)
    if total_len == 0: return 0
    density = note_count / total_len
    if 0.6 <= density <= 0.9: return 10
    elif density > 0.95: return -10
    elif density < 0.4: return -10
    else: return 0

# ==========================================
# 4. 总分计算
# ==========================================

def get_fitness(melody):
    if sum(melody) == 0: return -9999
    
    s_chords   = fitness_chords(melody)
    s_interval = fitness_intervals(melody)
    s_variety  = fitness_variety(melody)
    s_cadence  = fitness_cadence(melody)
    s_gap      = fitness_gap_fill(melody)
    s_inertia  = fitness_melodic_inertia(melody) # 新增项
    s_range    = fitness_range(melody)
    s_density  = fitness_rhythm_density(melody)
    
    # 调整权重：稍微提高 interval 和 inertia 的比重，强调连贯性
    total_score = (3 * s_chords) + \
                  (1.2 * s_interval) + \
                  (0.5 * s_variety) + \
                  (2.0 * s_cadence) + \
                  (1.5 * s_gap) + \
                  (3 * s_inertia) + \
                  (0.5 * s_range) + \
                  (0.8 * s_density)
                  
    return total_score