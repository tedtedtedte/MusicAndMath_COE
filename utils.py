# utils.py
import random
from midiutil import MIDIFile
import config  # 导入配置

def generate_random_melody(length=config.TOTAL_STEPS):
    """根据配置生成随机基因"""
    melody = []
    for _ in range(length):
        if random.random() < config.REST_PROB:
            note = 0
        else:
            note = random.randint(config.PITCH_MIN, config.PITCH_MAX)
        melody.append(note)
    return melody

def save_melody_to_midi(melody, filename="output.mid", tempo=120):
    """
    保存 MIDI 文件 (包含连音处理 & 和弦伴奏)
    """
    track = 0
    # --- 【关键修改】定义两个不同的通道 ---
    channel_melody = 0  # 旋律通道
    channel_chord = 1   # 和弦伴奏通道 (避开冲突)
    
    time = 0
    volume = 100
    step_duration = 0.25 # 十六分音符
    
    MyMIDI = MIDIFile(1) # 创建1个轨道
    MyMIDI.addTempo(track, time, tempo)
    
    # --- 1. 旋律写入 (使用 channel_melody) ---
    if len(melody) > 0:
        current_pitch = melody[0]
        current_length = 1
        current_start = 0
    
    for i in range(1, len(melody)):
        note = melody[i]
        if note == current_pitch and note != 0:
            current_length += 1
        else:
            if current_pitch != 0:
                # 注意这里使用的是 channel_melody
                MyMIDI.addNote(track, channel_melody, current_pitch, 
                               current_start * step_duration, 
                               current_length * step_duration, volume)
            current_pitch = note
            current_length = 1
            current_start = i
            
    # 写入最后一个音
    if current_pitch != 0:
        MyMIDI.addNote(track, channel_melody, current_pitch, 
                       current_start * step_duration, 
                       current_length * step_duration, volume)
            
    # --- 2. 写入背景和弦 (使用 channel_chord) ---
    for i, root in enumerate(config.CHORD_ROOTS):
        start_time = i * config.CHORD_DURATION
        # 注意：这里必须使用 channel_chord，而不是原来的 channel
        # 根音
        MyMIDI.addNote(track, channel_chord, root, start_time, config.CHORD_DURATION, 70)
        # 三音
        MyMIDI.addNote(track, channel_chord, root+4, start_time, config.CHORD_DURATION, 70)
        # 五音
        MyMIDI.addNote(track, channel_chord, root+7, start_time, config.CHORD_DURATION, 70)

    with open(filename, "wb") as f:
        MyMIDI.writeFile(f)
    print(f"Saved MIDI to: {filename}")