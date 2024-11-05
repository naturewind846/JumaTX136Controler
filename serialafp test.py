import tkinter as tk
import serial

# 设置串口参数
SERIAL_PORT = 'COM3'  # 请根据你的串口调整
BAUD_RATE = 115200

# 创建串口对象
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

# 控制发送状态
is_sending = False

def start_sending():
    global is_sending
    is_sending = True
    send_data()

def stop_sending():
    global is_sending
    if is_sending:
        is_sending = False
        ser.write(b'R\r')  # 发送停止命令
        print("已发送停止命令: R\r")

def send_data():
    global is_sending
    if is_sending:
        # 获取滑块的值
        slider_value = slider.get()
        # 构造发送的字符串
        message = f"T{slider_value * 1000}\r"
        ser.write(message.encode())
        print(f"发送: {message.strip()}")  # 打印发送的内容到终端
        # 每100ms发送一次
        root.after(20, send_data)

def update_slider_range():
    try:
        min_value = int(min_entry.get())
        max_value = int(max_entry.get())
        slider.config(from_=min_value, to=max_value)
        slider.set(min_value)  # 设置滑块初始位置
    except ValueError:
        pass  # 如果输入不合法，忽略

# 创建主窗口
root = tk.Tk()
root.title("串口发送控制")
root.geometry("400x250")

# 创建控件框架
frame = tk.Frame(root)
frame.pack(pady=10)

# 滑块
slider = tk.Scale(frame, from_=200, to=4000, orient=tk.HORIZONTAL, length=300)
slider.grid(row=0, column=0, columnspan=3, padx=5)

# 显示当前滑块值
slider_value_label = tk.Label(frame, text="当前值: 200", font=("Arial", 14))
slider_value_label.grid(row=1, column=0, columnspan=3, pady=5)

def update_label():
    slider_value_label.config(text=f"当前值: {slider.get()}")

slider.config(command=lambda value: update_label())  # 更新标签以显示当前滑块值

# 输入框和标签放在同一行
min_label = tk.Label(frame, text="最小值:")
min_label.grid(row=2, column=0, sticky=tk.E)
min_entry = tk.Entry(frame, width=5)
min_entry.grid(row=2, column=1, sticky=tk.W)

max_label = tk.Label(frame, text="最大值:")
max_label.grid(row=2, column=2, sticky=tk.E)
max_entry = tk.Entry(frame, width=5)
max_entry.grid(row=2, column=3, sticky=tk.W)

# 设置范围按钮
set_range_button = tk.Button(frame, text="设置范围", command=update_slider_range)
set_range_button.grid(row=3, columnspan=4, pady=5)

# 控制按钮框架
control_frame = tk.Frame(root)
control_frame.pack(pady=5)

# 创建开始发送按钮
start_button = tk.Button(control_frame, text="开始发送", command=start_sending)
start_button.grid(row=0, column=0, padx=5)

# 创建停止发送按钮
stop_button = tk.Button(control_frame, text="停止发送", command=stop_sending)
stop_button.grid(row=0, column=1, padx=5)

# 进入主循环
root.mainloop()

# 关闭串口
ser.close()
