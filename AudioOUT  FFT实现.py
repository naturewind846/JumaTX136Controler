import pyaudio
import numpy as np
from scipy.fftpack import fft
import serial
import time
import msvcrt  # 用于捕获键盘输入

# 配置音频和串口参数
RATE = 48000  # 采样率
CHUNK = int(RATE * 0.01)  # 保持原有的 CHUNK 大小
BUFFER_SIZE = 2  # 缓冲区大小，包含多少个 20ms 的样本
LOW_FREQ = 200  # 频率下限
HIGH_FREQ = 2100  # 频率上限
THRESHOLD = 25  # 幅度阈值
THRESHOLD_STOP = 3  # 立即停止阈值

# 初始化缓冲区和串口参数
buffer = np.zeros(BUFFER_SIZE * CHUNK, dtype=np.float32)
last_amplitudes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # 用于计算幅度阈值
serial_port = None  # 串口对象
is_sending = False  # 当前是否正在发送数据

def list_microphones():
    """列出可用的麦克风设备"""
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
    """从音频数据中提取主频率和其对应的幅值"""
    # 使用32位浮点数进行FFT计算
    fft_data = fft(data.astype(np.float32))  # 转换为浮点数进行FFT
    freqs = np.fft.fftfreq(len(data), 1.0 / rate)
    magnitudes = np.abs(fft_data)
    
    # 只考虑特定范围内的频率
    mask = (freqs >= LOW_FREQ) & (freqs <= HIGH_FREQ)
    freqs = freqs[mask]
    magnitudes = magnitudes[mask]
    
    if len(magnitudes) > 0:
        peak_index = np.argmax(magnitudes)
        peak_freq = freqs[peak_index]
        peak_magnitude = magnitudes[peak_index]
        return peak_freq, peak_magnitude
    else:
        return None, None

def calculate_amplitude_threshold(last_amplitudes, current_amplitude):
    """根据历史幅值和当前幅值计算整数阈值"""
    # 计算幅值的整数平均值
    avg_amplitude = sum(last_amplitudes) // len(last_amplitudes)  # 使用整数平均
    return (current_amplitude * 15 + avg_amplitude * 15) // 100  # 返回整数阈值

def audio_stream(device_index, port, baudrate):
    """开启音频流并控制频率输出到串口"""
    global is_sending, serial_port, last_amplitudes, buffer  # 添加 buffer 的 global 声明
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paFloat32,  # 采样格式为 16 位整数
        channels=1,
        rate=RATE,
        input=True,
        input_device_index=device_index,
        frames_per_buffer=CHUNK
    )
    
    # 打开串口
    serial_port = serial.Serial(port, baudrate)
    print("串口已连接，按空格开始/停止发送，按 S 停止所有发送。")

    try:
        while True:
            # 检查键盘输入
            if msvcrt.kbhit():
                key = msvcrt.getch().decode('utf-8').lower()
                if key == ' ':
                    is_sending = not is_sending
                    if not is_sending:
                        serial_port.write(b'R\r')
                        print("停止发送频率数据")
                elif key == 's':
                    print("终止所有输出，连续发送三次 'R\\r'")
                    for _ in range(3):
                        serial_port.write(b'R\r')
                    break

            # 读取 CHUNK 数据并填充缓冲区
            data = np.frombuffer(stream.read(CHUNK), dtype=np.float32)  # 直接读取 16 位整数
            buffer = np.roll(buffer, -CHUNK)
            buffer[-CHUNK:] = data

            # 计算当前缓冲区内的频率和幅度
            frequency, amplitude = get_frequency_and_amplitude(buffer, RATE)
            if frequency and amplitude:
                # 更新幅度历史
                last_amplitudes = last_amplitudes[1:] + [amplitude]
                amplitude_threshold = calculate_amplitude_threshold(last_amplitudes, amplitude)

                # 判断是否输出到串口
                if is_sending:
                    if amplitude >= THRESHOLD or (amplitude_threshold >= THRESHOLD and amplitude >= THRESHOLD_STOP):
                        if LOW_FREQ <= frequency <= HIGH_FREQ:
                            # 输出频率数据，格式 "Txxxxxxx\r"，频率扩大1000倍
                            freq_to_send = f"T{int(frequency * 1000)}\r".encode('utf-8')
                            serial_port.write(freq_to_send)
                            # 在这里使用 int() 函数显示幅度作为整数
                            print(f"发送频率: {freq_to_send.decode('utf-8').strip()} 当前幅值: {int(amplitude)}")
                        else:
                            # 频率不在范围内
                            print("频率不在范围内")
                    else:
                        # 平均幅度小于阈值，停止发送并输出当前阈值
                        serial_port.write(b'R\r')
                        # 在这里使用 int() 函数显示幅度作为整数
                        print(f"幅度小于阈值 {int(amplitude)}")


    except KeyboardInterrupt:
        print("录音结束")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        if serial_port:
            serial_port.close()
            print("串口已关闭")

# 主程序
if __name__ == "__main__":
    print("可用麦克风设备：")
    devices = list_microphones()
    device_index = int(input("请选择麦克风设备的索引号："))

    # 选择串口和波特率
    port = input("请输入串口号（如 COM3）：")
    baudrate = int(input("请输入波特率（如 9600）："))
    
    # 开始音频和串口控制
    audio_stream(device_index, port, baudrate)
