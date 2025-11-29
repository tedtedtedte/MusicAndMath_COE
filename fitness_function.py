# fitness_function.py

# ==========================================
# 1. 基础乐理常数与定义
# ==========================================
import config # 确保引入配置以动态计算步数

SCALE_C_MAJOR = {0, 2, 4, 5, 7, 9, 11} 
MIN_PITCH = 60
MAX_PITCH = 84

# 和弦定义 (I - V - vi - IV)
CHORD_C  = {0, 4, 7}   
CHORD_G  = {7, 11, 2}  
CHORD_Am = {9, 0, 4}   
CHORD_F  = {5, 9, 0}   

def get_chord_set(step_index):
    """
    根据当前时间步返回对应的和弦集合
    动态计算每小节步数，防止改了 config 后和弦错位
    """
    # 动态计算：每小节有多少步 = 4拍 * 每拍2步 = 8步
    steps_per_bar = config.BEATS_PER_BAR * config.STEPS_PER_BEAT
    bar = step_index // steps_per_bar 
    
    if bar == 0: return CHORD_C
    elif bar == 1: return CHORD_G
    elif bar == 2: return CHORD_Am
    elif bar == 3: return CHORD_F
    return CHORD_C

# ==========================================
# 2. 基础规则 (正确性)
# ==========================================

def fitness_chords(melody):
    """
    和弦贴合度
    """
    score = 0
    steps_per_beat = config.STEPS_PER_BEAT
    for i, note in enumerate(melody):
        if note == 0: continue
        target_chord = get_chord_set(i)
        note_class = note % 12
        # 动态判断强拍。
        # 如果是8分音符(steps=2)，每2步就是一拍(强位置)；
        # 为了更严谨，通常Beat 1和Beat 3(即第0拍和第2拍)是重音。
        # 这里简化逻辑：每拍的正拍位置都视为“强位置”，需要贴合和弦
        is_on_beat = (i % steps_per_beat == 0)
        if is_on_beat:
            # --- 正拍逻辑 (严格) ---
            if note_class in target_chord:
                score += 10   # 完美：和弦内音
            elif note_class in SCALE_C_MAJOR:
                score += 0    # 勉强：调内音但非和弦音 (不奖不罚，促使它去寻找和弦音)
            else:
                score -= 50   # [重罚]：正拍离调
        else:
            # --- 弱拍/反拍逻辑 (稍宽容) ---
            # 弱拍允许经过音，但必须在调内
            if note_class in target_chord:
                score += 5    # 和弦内音依然最好
            elif note_class in SCALE_C_MAJOR:
                score += 2    # 调内经过音 (Scale Tone) 可以接受
            else:
                score -= 30   # [重罚]：弱拍也不允许出现调外音   
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
    """终止感"""
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
                score -= 7
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

def fitness_climax_control(melody):
    """
    高潮：限制高音频率，防止喧宾夺主。
    逻辑：高音区的音符应该作为“高潮”稀缺存在，而不是常态。
    """
    # 定义高音阈值：我们设定为最高允许音高 (84) 往下的一个区间
    # 例如 77 (F5) 以上被视为“高潮音区”
    CLIMAX_THRESHOLD = MAX_PITCH - 7 
    notes = [n for n in melody if n != 0]
    total_notes = len(notes)
    if total_notes == 0: return 0
    # 统计高音数量
    high_note_count = sum(1 for n in notes if n > CLIMAX_THRESHOLD)
    ratio = high_note_count / total_notes
    score = 0
    # --- 评分逻辑 ---
    # 1. 黄金比例 (5% - 15%): 
    # 在64个音符中，大约有3-10个高音。这是理想的。
    if 0.05 <= ratio <= 0.15:
        score = 15  # 给予高分奖励
    # 2. 高音泛滥 (> 20%): 
    # 听起来很累，惩罚
    elif ratio > 0.20:
        score = -20    
    # 3. 完全没有高音 (0%): 
    # 过于平淡，压抑。给予惩罚，鼓励尝试突破
    elif ratio == 0:
        score = -20
    # 其他情况 (1%-5% 或 15%-20%) 属于过渡区，不奖不罚
    return score

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
    s_inertia  = fitness_melodic_inertia(melody)
    s_range    = fitness_range(melody)
    s_density  = fitness_rhythm_density(melody)
    s_climax = fitness_climax_control(melody)
    
    # 调整权重：稍微提高 interval 和 inertia 的比重，强调连贯性
    total_score = (2.5 * s_chords) + \
                  (0.5 * s_interval) + \
                  (0.5 * s_variety) + \
                  (2.0 * s_cadence) + \
                  (1.5 * s_gap) + \
                  (7 * s_inertia) + \
                  (0.5 * s_range) + \
                  (10 * s_density) + \
                  (1.2 * s_climax)
                  
    return total_score