import serial
import time

# 配置参数
PORT_A = 'COM19'  # 串口 A，用于读取 CTS 和 DSR
PORT_B = 'COM20'  # 串口 B，用于发送指令
BAUD_RATE = 115200  # 两个串口的波特率

space_freq = 1450000  # Space频率
shift_freq = 1550000  # Shift频率
poll_interval = 0.005  # 轮询间隔，单位：秒

def send_command(ser_b, command):
    """发送指令到串口 B"""
    ser_b.write(command.encode())
    print(f"发送到串口 B 的指令: {command.strip()}")

def main():
    try:
        # 打开串口 A 和 B
        ser_a = serial.Serial(PORT_A, BAUD_RATE)
        ser_b = serial.Serial(PORT_B, BAUD_RATE)
        print(f"已连接到 {PORT_A} 和 {PORT_B}，波特率 {BAUD_RATE}")

        # 初始化状态
        last_cts_state = ser_a.cts  # 初始化 CTS 状态
        last_dsr_state = ser_a.dsr  # 初始化 DSR 状态

        while True:
            # 获取串口 A 的当前 CTS 和 DSR 状态
            cts_state = ser_a.cts
            dsr_state = ser_a.dsr

            # 检测 CTS 逻辑
            if cts_state != last_cts_state:  # 只有 CTS 状态变化时处理
                if cts_state:  # 发射状态
                    print("CTS切换到高，进入发射状态。")
                else:  # 禁止发射状态
                    print("CTS从高变低，发送R指令。")
                    send_command(ser_b, "R\r\n")
                last_cts_state = cts_state  # 更新 CTS 状态

            # 检测 DSR 逻辑（仅当 CTS 为高时才处理）
            if cts_state:  # 仅发射状态下处理 DSR
                if dsr_state != last_dsr_state:  # 只有 DSR 状态变化时处理
                    if dsr_state:  # DSR从低到高
                        print("DSR从低变高，发射shift频率。")
                        send_command(ser_b, f"T{shift_freq:07d}\r\n")
                    else:  # DSR从高到低
                        print("DSR从高变低，发射space频率。")
                        send_command(ser_b, f"T{space_freq:07d}\r\n")
                    last_dsr_state = dsr_state  # 更新 DSR 状态

            # 轮询间隔
            time.sleep(poll_interval)

    except serial.SerialException as e:
        print(f"串口错误: {e}")
    except KeyboardInterrupt:
        print("程序已停止。")
    finally:
        # 关闭串口
        if 'ser_a' in locals() and ser_a.is_open:
            ser_a.close()
        if 'ser_b' in locals() and ser_b.is_open:
            ser_b.close()
        print("已关闭串口。")

if __name__ == "__main__":
    main()
