# 这个PY程序用于电脑控制JUMA TX136的REMOTE AFP。
# 使用VB-Audio Virtual Cable、选择串口、波特率，可以实时解析fsk音频的频率并发送至juma tx136

import pyaudio
import numpy as np
from scipy.fftpack import fft
import serial
import msvcrt  # 用于捕获键盘输入
import time

# 配置音频和串口参数
RATE = 96000
CYCLE = 20
CHUNK = int(RATE * CYCLE / 1000)
BUFFER_SIZE = 5
LOW_FREQ = 200 
HIGH_FREQ = 2100 
THRESHOLD = 100
THRESHOLD_STOP = 10
ZERO_PADDING_FACTOR = 16

buffer = np.zeros(BUFFER_SIZE * CHUNK, dtype=np.float32)
last_amplitudes = [0] * 10
serial_port = None
is_sending = False
last_sent_frequency = None

last_display_time = 0  # 上次屏幕刷新时间
DISPLAY_INTERVAL = 0.02  # 每0.1秒刷新一次

def list_microphones():
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    devices = []
    for i in range(0, numdevices):
        dev = p.get_device_info_by_host_api_device_index(0, i)
        if dev.get('maxInputChannels') > 0:
            devices.append((i, dev.get('name')))
            print(f"设备索引：{i}, 设备名称：{dev.get('name')}")
    p.terminate()
    return devices

def get_frequency_and_amplitude(data, rate):
    # 执行FFT计算
    padded_data = np.pad(data, (0, len(data) * (ZERO_PADDING_FACTOR - 1)), 'constant')
    fft_data = fft(padded_data)
    
    # 选择目标频段
    freqs = np.fft.fftfreq(len(padded_data), 1.0 / rate)
    magnitudes = np.abs(fft_data)
    mask = (freqs >= LOW_FREQ) & (freqs <= HIGH_FREQ)
    freqs = freqs[mask]
    magnitudes = magnitudes[mask]

    if len(magnitudes) > 0:
        peak_index = np.argmax(magnitudes)
        
        if 1 <= peak_index < len(magnitudes) - 1:
            alpha = magnitudes[peak_index - 1]
            beta = magnitudes[peak_index]
            gamma = magnitudes[peak_index + 1]
            delta = 0.5 * (alpha - gamma) / (alpha - 2 * beta + gamma)
            interpolated_freq = freqs[peak_index] + delta * (freqs[1] - freqs[0])
            interpolated_magnitude = beta - 0.25 * (alpha - gamma) * delta
        else:
            interpolated_freq = freqs[peak_index]
            interpolated_magnitude = magnitudes[peak_index]

        return interpolated_freq, interpolated_magnitude
    else:
        return None, None

def calculate_amplitude_threshold(last_amplitudes, current_amplitude):
    avg_amplitude = sum(last_amplitudes) // len(last_amplitudes)
    return (current_amplitude * 6 + avg_amplitude * 24) // 30

def send_frequency_to_serial(frequency, amplitude, amplitude_threshold):
    global last_sent_frequency
    if amplitude >= THRESHOLD or (amplitude_threshold >= THRESHOLD and amplitude >= THRESHOLD_STOP):
        if LOW_FREQ <= frequency <= HIGH_FREQ:
            if last_sent_frequency != int(frequency):
                freq_to_send = f"T{int(frequency * 1000)}\r".encode('utf-8')
                serial_port.write(freq_to_send)
                last_sent_frequency = int(frequency)
        else:
            serial_port.write(b'R\r')
            last_sent_frequency = None
    else:
        serial_port.write(b'R\r')
        last_sent_frequency = None

def audio_stream(device_index, port, baudrate):
    global is_sending, serial_port, last_amplitudes, buffer, last_display_time
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paFloat32,  
        channels=1,
        rate=RATE,
        input=True,
        input_device_index=device_index,
        frames_per_buffer=CHUNK
    )
    
    serial_port = serial.Serial(port, baudrate)
    print("串口已连接，按空格控制发送/显示，按 S 停止所有发送。")

    try:
        while True:
            if msvcrt.kbhit():
                key = msvcrt.getch().decode('utf-8').lower()
                if key == ' ':
                    is_sending = not is_sending
                    if not is_sending:
                        serial_port.write(b'R\r')
                        print("\r停止发送和显示频率数据                                          ")
                elif key == 's':
                    print("\r终止所有输出，发送三次 'R\\r' 停止信号")
                    for _ in range(3):
                        serial_port.write(b'R\r')
                    break

            data = np.frombuffer(stream.read(CHUNK), dtype=np.float32)
            buffer = np.roll(buffer, -CHUNK)
            buffer[-CHUNK:] = data

            frequency, amplitude = get_frequency_and_amplitude(buffer, RATE)
            if frequency and amplitude:
                last_amplitudes = last_amplitudes[1:] + [amplitude]
                amplitude_threshold = calculate_amplitude_threshold(last_amplitudes, amplitude)
                
                if is_sending:
                    # 仅在0.1秒间隔内显示输出，减少屏幕刷新频率
                    current_time = time.time()
                    if current_time - last_display_time >= DISPLAY_INTERVAL:
                        last_display_time = current_time
                        status = " 发射中 " if amplitude >= THRESHOLD else " 等待中 "
                        print(f"\r({status})当前频率: {frequency:.2f} Hz, 幅度: {amplitude:.2f}, 平均幅度: {amplitude_threshold}     ", end='')
                    
                    # 将频率数据发送到串口
                    send_frequency_to_serial(frequency, amplitude, amplitude_threshold)

    except KeyboardInterrupt:
        print("\r录音结束")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        if serial_port:
            serial_port.close()
            print("\r串口已关闭")

# 主程序
if __name__ == "__main__":
    print("这个PY程序用于电脑控制JUMA TX136的REMOTE AFP")
    print("使用VB-Audio Virtual Cable、选择串口、波特率，可以实时解析fsk音频的频率并通过串口发送")
    print("可用麦克风设备：")
    devices = list_microphones()
    device_index = int(input("请选择麦克风设备的索引号："))
    
    port = input("请输入串口号（如 COM3）：")
    baudrate = int(input("请输入波特率（如 9600）："))
    
    audio_stream(device_index, port, baudrate)
