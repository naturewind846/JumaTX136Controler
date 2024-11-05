import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedStyle
import serial
import serial.tools.list_ports
import time
 
class SerialControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Juma TX136控制程序 BH3PTS 20241102")
        
        self.serial_port = None
        self.frequency = 136000  # 初始频率
        
        # 串口设置框
        self.port_frame = ttk.LabelFrame(root, text="串口设置")
        self.port_frame.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')

        self.toggle_button = ttk.Button(self.port_frame, text="打开串口", command=self.toggle_serial)
        self.toggle_button.grid(row=0, column=0, padx=5, pady=5)

        self.port_combobox = ttk.Combobox(self.port_frame, values=self.list_ports(), width=8)
        self.port_combobox.grid(row=0, column=1, padx=5, pady=5)

        self.baudrate_label = ttk.Label(self.port_frame, text="波特率: ")
        self.baudrate_label.grid(row=1, column=0, padx=5, pady=5)

        self.baudrate_combobox = ttk.Combobox(self.port_frame, values=[1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200], width=8)
        self.baudrate_combobox.set(9600)
        self.baudrate_combobox.grid(row=1, column=1, padx=5, pady=5)

        self.debug_button = ttk.Button(self.port_frame, text="调试模式", command=self.open_debug_window, state='disabled')
        self.debug_button.grid(row=2, column=0, padx=5, pady=5)

        self.firmware_button = ttk.Button(self.port_frame, text="固件信息",command=self.send_firmware_info, state='disabled')
        self.firmware_button.grid(row=2, column=1, padx=5, pady=5)

        # 创建频率设置框
        self.frequency_frame = ttk.LabelFrame(root, text="频率设置")
        self.frequency_frame.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')

        self.current_frequency_label = ttk.Label(self.frequency_frame, text="当前频率:")
        self.current_frequency_label.grid(row=0, column=0, padx=5, pady=5)

        self.current_frequency_value = tk.StringVar(value=f"{self.frequency} Hz")
        self.current_frequency_display = ttk.Label(self.frequency_frame, textvariable=self.current_frequency_value, font=("Arial", 32))
        self.current_frequency_display.grid(row=0, column=1, columnspan=2, padx=5, pady=5)

        self.new_frequency_label = ttk.Label(self.frequency_frame, text="输入频率:")
        self.new_frequency_label.grid(row=1, column=0, padx=5, pady=5)

        self.frequency_entry = ttk.Entry(self.frequency_frame, width=14)
        self.frequency_entry.grid(row=1, column=1, padx=5, pady=5)
        self.frequency_entry.config(state='disabled')
        self.frequency_entry.bind("<Return>", lambda event: self.set_frequency())

        self.set_frequency_button = ttk.Button(self.frequency_frame, text="设置", command=self.set_frequency, state='disabled')
        self.set_frequency_button.grid(row=1, column=2, padx=5, pady=5)

        # 基础控制区域
        self.control_frame = ttk.LabelFrame(root, text="基础控制")
        self.control_frame.grid(row=1, column=0, padx=5, pady=5, sticky='nsew')

        # 模式切换
        self.mode_label = ttk.Label(self.control_frame, text="模式切换:")
        self.mode_label.grid(row=0, column=0, padx=5, pady=5)

        self.mode_combobox = ttk.Combobox(self.control_frame, values=["CW", "QRSS", "DFCW", "JASON", "WSQ2", "OPERA", "WSPR", "FST4W", "JT9", "SCRIPT", "REMOTE"], width=10)
        self.mode_combobox.set("CW")
        self.mode_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.mode_combobox.bind("<<ComboboxSelected>>", self.change_mode)

        # 前置放大器设置
        self.preamplifier_label = ttk.Label(self.control_frame, text="前置放大器:")
        self.preamplifier_label.grid(row=1, column=0, padx=5, pady=5)

        self.preamplifier_combobox = ttk.Combobox(self.control_frame, values=["OFF", "10 dB", "20 dB"], width=10)
        self.preamplifier_combobox.set("OFF")
        self.preamplifier_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.preamplifier_combobox.bind("<<ComboboxSelected>>", self.set_preamplifier)

        # 接收上变频设置
        self.upconverter_label = ttk.Label(self.control_frame, text="接收上变频:")
        self.upconverter_label.grid(row=2, column=0, padx=5, pady=5)

        self.upconverter_combobox = ttk.Combobox(self.control_frame, values=["OFF", "ON"], width=10)
        self.upconverter_combobox.set("OFF")
        self.upconverter_combobox.grid(row=2, column=1, padx=5, pady=5)
        self.upconverter_combobox.bind("<<ComboboxSelected>>", self.set_upconverter)

        # CW电键模式设置
        self.cw_mode_label = ttk.Label(self.control_frame, text="CW电键模式:")
        self.cw_mode_label.grid(row=3, column=0, padx=5, pady=5)

        self.cw_mode_combobox = ttk.Combobox(self.control_frame, values=["Dot priority", "Iambic A", "Iambic B", "Straight", "Beacon"], width=10)
        self.cw_mode_combobox.set("Dot priority")
        self.cw_mode_combobox.grid(row=3, column=1, padx=5, pady=5)
        self.cw_mode_combobox.bind("<<ComboboxSelected>>", self.set_cw_mode)

        # CW识别发送
        self.cw_identity_label = ttk.Label(self.control_frame, text="识别CW发送:")
        self.cw_identity_label.grid(row=4, column=0, padx=5, pady=5)

        self.cw_identity_combobox = ttk.Combobox(self.control_frame, values=["OFF", "12 wpm", "24 wpm"], width=10)
        self.cw_identity_combobox.set("OFF")
        self.cw_identity_combobox.grid(row=4, column=1, padx=5, pady=5)
        self.cw_identity_combobox.bind("<<ComboboxSelected>>", self.send_cw_identity)

        # 操作模式设置
        self.operation_mode_label = ttk.Label(self.control_frame, text="操作模式:")
        self.operation_mode_label.grid(row=5, column=0, padx=5, pady=5)

        self.operation_mode_combobox = ttk.Combobox(self.control_frame, values=["Stand By", "Operation", "Tune"], width=10)
        self.operation_mode_combobox.set("Stand By")
        self.operation_mode_combobox.grid(row=5, column=1, padx=5, pady=5)
        self.operation_mode_combobox.bind("<<ComboboxSelected>>", self.set_operation_mode)

        # 发射功率设置
        self.power_label = ttk.Label(self.control_frame, text="发射功率:")
        self.power_label.grid(row=6, column=0, padx=5, pady=5)

        self.power_combobox = ttk.Combobox(self.control_frame, values=["MIN", "LOW", "HIGH", "MAX"], width=10)
        self.power_combobox.set("MIN")
        self.power_combobox.grid(row=6, column=1, padx=5, pady=5)
        self.power_combobox.bind("<<ComboboxSelected>>", self.set_power)
        
        # TX Control设置
        self.tx_control_label = ttk.Label(self.control_frame, text="TX控制方式:")
        self.tx_control_label.grid(row=7, column=0, padx=5, pady=5)
        self.tx_control_combobox = ttk.Combobox(self.control_frame, values=["Auto", "MOX", "RTS 悬空会发射"], width=10)
        self.tx_control_combobox.set("Auto")
        self.tx_control_combobox.grid(row=7, column=1, padx=5, pady=5)
        self.tx_control_combobox.bind("<<ComboboxSelected>>", self.send_tx_control_setting)

        # SPARE I/O设置
        self.spare_io_label = ttk.Label(self.control_frame, text="SPARE I/O:")
        self.spare_io_label.grid(row=8, column=0, padx=5, pady=5)
        self.spare_io_combobox = ttk.Combobox(self.control_frame, values=["OFF", "ON"], width=10)
        self.spare_io_combobox.grid(row=8, column=1, padx=5, pady=5)
        self.spare_io_combobox.bind("<<ComboboxSelected>>", self.send_spare_io_setting)

        # 二选一设置
        self.bi_band_label = ttk.Label(self.control_frame, text="TX136-500板卡安装:")
        self.bi_band_label.grid(row=9, column=0, padx=5, pady=5)
        self.bi_band_var = tk.IntVar()
        self.bi_band_off_radio = ttk.Radiobutton(self.control_frame, text="已安装", variable=self.bi_band_var, value=1, command=self.update_spare_io_options)
        self.bi_band_off_radio.grid(row=10, column=0, padx=5, pady=5)
        self.bi_band_on_radio = ttk.Radiobutton(self.control_frame, text="未安装", variable=self.bi_band_var, value=0, command=self.update_spare_io_options)
        self.bi_band_on_radio.grid(row=10, column=1, padx=5, pady=5)
        self.update_spare_io_options()

        # 参数同步和时间同步
        self.sync_button = ttk.Button(self.control_frame, text="参数同步", command=self.request_current_settings)
        self.sync_button.grid(row=11, column=0, padx=5, pady=5)

        self.time_sync_button = ttk.Button(self.control_frame, text="时间同步", command=self.send_time_sync)
        self.time_sync_button.grid(row=11, column=1, padx=5, pady=5)

        # 进阶控制区域
        self.advanced_control_frame = ttk.LabelFrame(root, text="进阶控制")
        self.advanced_control_frame.grid(row=1, column=1, padx=5, pady=5, sticky='nsew')

        # 呼号输入
        self.callsign_label = ttk.Label(self.advanced_control_frame, text="呼号:")
        self.callsign_label.grid(row=0, column=0, padx=5, pady=5)
        self.callsign_entry = ttk.Entry(self.advanced_control_frame, width=10)
        self.callsign_entry.grid(row=0, column=1, padx=5, pady=5)
        self.callsign_entry.bind("<Return>", lambda event: self.send_callsign())  # 绑定回车事件
        self.callsign_button = ttk.Button(self.advanced_control_frame, text="上传呼号", command=self.send_callsign)
        self.callsign_button.grid(row=0, column=2, padx=5, pady=5)

        # 网格坐标输入
        self.grid_label = ttk.Label(self.advanced_control_frame, text="网格坐标:")
        self.grid_label.grid(row=1, column=0, padx=5, pady=5)
        self.grid_entry = ttk.Entry(self.advanced_control_frame, width=10)
        self.grid_entry.grid(row=1, column=1, padx=5, pady=5)
        self.grid_entry.bind("<Return>", lambda event: self.send_grid())  # 绑定回车事件
        self.grid_button = ttk.Button(self.advanced_control_frame, text="上传网格坐标", command=self.send_grid)
        self.grid_button.grid(row=1, column=2, padx=5, pady=5)

        # CW速度输入
        self.cw_speed_label = ttk.Label(self.advanced_control_frame, text="CW码率:")
        self.cw_speed_label.grid(row=2, column=0, padx=5, pady=5)
        self.cw_speed_combobox = ttk.Combobox(self.advanced_control_frame, values=[str(i) for i in range(1, 51)], width=10)
        self.cw_speed_combobox.grid(row=2, column=1, padx=5, pady=5)
        self.cw_speed_combobox.bind("<<ComboboxSelected>>", self.send_cw_speed)

        # CW信标文本输入
        self.cw_beacon_label = ttk.Label(self.advanced_control_frame, text="CW信标文本:")
        self.cw_beacon_label.grid(row=3, column=0, padx=5, pady=5)
        self.cw_beacon_entry = ttk.Entry(self.advanced_control_frame, width=21)
        self.cw_beacon_entry.grid(row=3, column=1, padx=5, pady=5)
        self.cw_beacon_entry.bind("<Return>", lambda event: self.send_cw_beacon())  # 绑定回车事件
        self.cw_beacon_button = ttk.Button(self.advanced_control_frame, text="上传CW文本", command=self.send_cw_beacon)
        self.cw_beacon_button.grid(row=3, column=2, padx=5, pady=5)

        # 信标文本输入
        self.beacon_text_label = ttk.Label(self.advanced_control_frame, text="信标文本:")
        self.beacon_text_label.grid(row=4, column=0, padx=5, pady=5)
        self.beacon_text_entry = ttk.Entry(self.advanced_control_frame, width=21)
        self.beacon_text_entry.grid(row=4, column=1, padx=5, pady=5)
        self.beacon_text_entry.bind("<Return>", lambda event: self.send_beacon_text())  # 绑定回车事件
        self.beacon_text_button = ttk.Button(self.advanced_control_frame, text="上传信标文本", command=self.send_beacon_text)
        self.beacon_text_button.grid(row=4, column=2, padx=5, pady=5)

        # 自动脚本文本输入
        self.script_text_label = ttk.Label(self.advanced_control_frame, text="Script脚本:")
        self.script_text_label.grid(row=5, column=0, padx=5, pady=5)
        self.script_text_entry = ttk.Entry(self.advanced_control_frame, width=21)
        self.script_text_entry.grid(row=5, column=1, padx=5, pady=5)
        self.script_text_entry.bind("<Return>", lambda event: self.send_script_text())  # 绑定回车事件
        self.script_text_button = ttk.Button(self.advanced_control_frame, text="上传自动脚本", command=self.send_script_text)
        self.script_text_button.grid(row=5, column=2, padx=5, pady=5)

        # 在主应用程序类中添加一个按钮，用于打开QRSS DFCW设置窗口
        self.qrss_dfcw_button = ttk.Button(self.advanced_control_frame, text="QRSS DFCW设置", command=self.open_qrss_dfcw_window)
        self.qrss_dfcw_button.grid(row=6, column=0, padx=5, pady=5)

        # 在主应用程序类中添加一个按钮，用于打开Jason设置窗口
        self.jason_settings_button = ttk.Button(self.advanced_control_frame, text="Jason WSQ2设置", command=self.open_jason_settings_window)
        self.jason_settings_button.grid(row=6, column=1, padx=5, pady=5)

        # 在主应用程序类中添加一个按钮，用于打开Opera设置窗口
        self.opera_settings_button = ttk.Button(self.advanced_control_frame, text="Opera设置", command=self.open_opera_settings_window)
        self.opera_settings_button.grid(row=6, column=2, padx=5, pady=5)

        # 在主应用程序类中添加一个按钮，用于打开WSPR设置窗口
        self.wspr_button = ttk.Button(self.advanced_control_frame, text="WSPR设置", command=self.open_wspr_settings_window)
        self.wspr_button.grid(row=7, column=0, padx=5, pady=5)
        
        # 在主应用程序类中添加一个按钮，用于打开FST4W设置窗口
        self.fst4w_button = ttk.Button(self.advanced_control_frame, text="FST4W设置", command=self.open_fst4w_settings_window)
        self.fst4w_button.grid(row=7, column=1, padx=5, pady=5)

        # 添加 JT9 设置按钮
        self.jt9_button = ttk.Button(self.advanced_control_frame, text="JT9设置", command=self.open_jt9_settings_window)
        self.jt9_button.grid(row=7, column=2, padx=5, pady=5)

        # 在主应用程序类中添加按钮
        self.script_remote_button = ttk.Button(self.advanced_control_frame, text="Script Remote设置", command=self.open_script_remote_settings_window)
        self.script_remote_button.grid(row=8, column=1, padx=5, pady=5)


        # 输入信息框
        self.input_frame = ttk.LabelFrame(root, text="自定义信息发射（仅支持ASCII）")
        self.input_frame.grid(row=2, column=1, padx=5, pady=5, sticky='e')

        self.input_entry = ttk.Entry(self.input_frame, width=34)
        self.input_entry.grid(row=0, columnspan=3, padx=10, pady=10)
        self.input_entry.bind("<Return>", lambda event: self.send_input_info())

        # 按钮: 发送输入信息, 发送机载信息, 停止发射
        self.send_input_button = ttk.Button(self.input_frame, text="发送输入信息", command=self.send_input_info)
        self.send_input_button.grid(row=1, column=0, padx=5, pady=5)

        self.send_onboard_button = ttk.Button(self.input_frame, text="发送机载信标", command=self.send_onboard_info)
        self.send_onboard_button.grid(row=1, column=1, padx=5, pady=5)

        self.stop_transmission_button = ttk.Button(self.input_frame, text="停止发射", command=self.stop_transmission)
        self.stop_transmission_button.grid(row=1, column=2, padx=5, pady=5)

        # 信息显示区域
        self.info_text = tk.Text(root, height=9, width=40, state='disabled')
        self.info_text.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky='nsw')

        self.scrollbar = ttk.Scrollbar(root, command=self.info_text.yview)
        
        # 状态栏
        self.status_frame = ttk.Frame(root)
        self.status_frame.grid(row=4, column=0, columnspan=3, pady=5, sticky='ew')  # 修改行号为4以放在底部

        self.voltage_label = ttk.Label(self.status_frame, text="电源电压: N/A")
        self.voltage_label.grid(row=0, column=0, padx=10)

        self.current_label = ttk.Label(self.status_frame, text="漏极电流: N/A")
        self.current_label.grid(row=0, column=1, padx=10)

        self.power_label = ttk.Label(self.status_frame, text="发射功率: N/A")
        self.power_label.grid(row=0, column=2, padx=10)

        self.swr_label = ttk.Label(self.status_frame, text="驻波比: N/A")
        self.swr_label.grid(row=0, column=3, padx=10)

        self.transmit_status_label = ttk.Label(self.status_frame, text="状态: N/A")
        self.transmit_status_label.grid(row=0, column=4, padx=10)

        self.update_status_ids = []


    def open_debug_window(self):
        """打开调试窗口"""
        self.debug_window = tk.Toplevel(self.root)
        self.debug_window.title("调试模式")

        self.command_entry = ttk.Entry(self.debug_window, width=35)
        self.command_entry.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        self.command_entry.bind("<Return>", lambda event: self.send_command())

        self.noneedcr_label = ttk.Label(self.debug_window, text="直接输入指令 不需要输入CR或者转义符")
        self.noneedcr_label.grid(row=1, columnspan=2, padx=10)


        send_button = ttk.Button(self.debug_window, text="发送", command=self.send_command)
        send_button.grid(row=2, column=0, padx=10, pady=5)

        exit_button = ttk.Button(self.debug_window, text="退出", command=self.close_debug_window)
        exit_button.grid(row=2, column=1,padx=10, pady=5)

    def open_qrss_dfcw_window(self):
        """打开QRSS DFCW设置窗口"""
        self.qrss_window = tk.Toplevel(self.root)
        self.qrss_window.title("QRSS DFCW设置")

        # 点时间设置
        dot_time_label = ttk.Label(self.qrss_window, text="点时间设置:")
        dot_time_label.grid(row=0, column=0, padx=5, pady=5)
        self.dot_time_combobox = ttk.Combobox(self.qrss_window, values=[str(i) for i in range(1, 121)], width=10)
        self.dot_time_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.dot_time_combobox.bind("<<ComboboxSelected>>", self.send_dot_time)  # 绑定选择事件

        # DFCW频移设置
        dfcw_shift_label = ttk.Label(self.qrss_window, text="DFCW频移设置:")
        dfcw_shift_label.grid(row=1, column=0, padx=5, pady=5)
        self.dfcw_shift_combobox = ttk.Combobox(self.qrss_window, values=[f"{i/10:.1f}" for i in range(1, 51)], width=10)  # 0.1 到 5.0
        self.dfcw_shift_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.dfcw_shift_combobox.bind("<<ComboboxSelected>>", self.send_dfcw_dash_shift)  # 绑定选择事件

        # 发送间隔设置
        cqd_frame_label = ttk.Label(self.qrss_window, text="发送间隔设置:")
        cqd_frame_label.grid(row=2, column=0, padx=5, pady=5)
        self.interval_combobox = ttk.Combobox(self.qrss_window, values=[
            "one play", "continuously", "1 timeslot out of 2", 
            "1 timeslot out of 3", "1 timeslot out of 4", "1 timeslot out of 5"
        ], width=20)
        self.interval_combobox.grid(row=2, column=1, padx=5, pady=5)
        self.interval_combobox.bind("<<ComboboxSelected>>", self.send_interval_setting)

    def open_jason_settings_window(self):
        """打开Jason WSQ2设置窗口"""
        self.jason_window = tk.Toplevel(self.root)
        self.jason_window.title("Jason WSQ2设置")

        # JASON发射帧设置
        jason_frame_label = ttk.Label(self.jason_window, text="Jason发射帧设置:")
        jason_frame_label.grid(row=0, column=0, padx=5, pady=5)
        self.jason_interval_combobox = ttk.Combobox(self.jason_window, values=[
            "one play", "continuously", "1 timeslot out of 2", 
            "1 timeslot out of 3", "1 timeslot out of 4", "1 timeslot out of 5"
        ], width=20)
        self.jason_interval_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.jason_interval_combobox.bind("<<ComboboxSelected>>", self.send_jason_interval_setting)

        # JASON速度设置
        speed_label = ttk.Label(self.jason_window, text="JASON速度设置:")
        speed_label.grid(row=1, column=0, padx=5, pady=5)
        self.jason_speed_combobox = ttk.Combobox(self.jason_window, values=[
            "Normal", "Normal turbo", "Fast", "Fast turbo"
        ], width=20)
        self.jason_speed_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.jason_speed_combobox.bind("<<ComboboxSelected>>", self.send_jason_speed_setting)

        # WSQ帧设置
        wsq_frame_label = ttk.Label(self.jason_window, text="WSQ帧设置:")
        wsq_frame_label.grid(row=2, column=0, padx=5, pady=5)
        self.wsq_frame_combobox = ttk.Combobox(self.jason_window, values=[
            "one play", "continuously", "1 timeslot out of 2", 
            "1 timeslot out of 3", "1 timeslot out of 4", "1 timeslot out of 5"
        ], width=20)
        self.wsq_frame_combobox.grid(row=2, column=1, padx=5, pady=5)
        self.wsq_frame_combobox.bind("<<ComboboxSelected>>", self.send_wsq_frame_setting)


    def open_opera_settings_window(self):
        """打开Opera设置窗口"""
        self.opera_window = tk.Toplevel(self.root)
        self.opera_window.title("Opera设置")

        # OPERA frame设置
        frame_label = ttk.Label(self.opera_window, text="OPERA Frame设置:")
        frame_label.grid(row=0, column=0, padx=5, pady=5)
        self.opera_frame_combobox = ttk.Combobox(self.opera_window, values=[
            "one play", "continuously", "1 timeslot out of 2", 
            "1 timeslot out of 3", "1 timeslot out of 4", "1 timeslot out of 5"
        ], width=20)
        self.opera_frame_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.opera_frame_combobox.bind("<<ComboboxSelected>>", self.send_opera_frame_setting)

        # OPERA速度设置
        speed_label = ttk.Label(self.opera_window, text="OPERA速度设置:")
        speed_label.grid(row=1, column=0, padx=5, pady=5)
        self.opera_speed_combobox = ttk.Combobox(self.opera_window, values=[
            "OPERA 2", "OPERA 4", "OPERA 8", "OPERA 16", "OPERA 32", "OPERA 65"
        ], width=20)
        self.opera_speed_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.opera_speed_combobox.bind("<<ComboboxSelected>>", self.send_opera_speed_setting)

    def open_wspr_settings_window(self):
        """打开WSPR设置窗口"""
        self.wspr_window = tk.Toplevel(self.root)
        self.wspr_window.title("WSPR设置")

        # GPS定位器选择
        gps_locator_label = ttk.Label(self.wspr_window, text="GPS定位器选择:")
        gps_locator_label.grid(row=0, column=0, padx=5, pady=5)
        self.gps_locator_combobox = ttk.Combobox(self.wspr_window, values=["OFF", "ON"], width=10)
        self.gps_locator_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.gps_locator_combobox.bind("<<ComboboxSelected>>", self.send_gps_locator_setting)

        # GPS定位器值
        gps_value_label = ttk.Label(self.wspr_window, text="GPS定位器值:")
        gps_value_label.grid(row=1, column=0, padx=5, pady=5)
        self.gps_value_result = ttk.Label(self.wspr_window, text="N/A", relief="sunken", width=15)
        self.gps_value_result.grid(row=1, column=1, padx=5, pady=5)
        gps_value_button = ttk.Button(self.wspr_window, text="获取GPS值", command=self.query_gps_value)
        gps_value_button.grid(row=1, column=2, padx=5, pady=5)

        # WSPR功率设置
        power_label = ttk.Label(self.wspr_window, text="WSPR功率 (0-60 dBm):")
        power_label.grid(row=2, column=0, padx=5, pady=5)
        self.power_combobox = ttk.Combobox(self.wspr_window, values=[str(i) for i in range(0, 61)], width=10)
        self.power_combobox.grid(row=2, column=1, padx=5, pady=5)
        self.power_combobox.bind("<<ComboboxSelected>>", self.send_wspr_power_setting)

        # WSPR速度设置
        speed_label = ttk.Label(self.wspr_window, text="WSPR速度:")
        speed_label.grid(row=3, column=0, padx=5, pady=5)
        self.wspr_speed_combobox = ttk.Combobox(self.wspr_window, values=["WSPR-2", "WSPR-15"], width=10)
        self.wspr_speed_combobox.grid(row=3, column=1, padx=5, pady=5)
        self.wspr_speed_combobox.bind("<<ComboboxSelected>>", self.send_wspr_speed_setting)

        # WSPR帧设置
        frame_label = ttk.Label(self.wspr_window, text="WSPR帧设置:")
        frame_label.grid(row=4, column=0, padx=5, pady=5)
        self.wspr_frame_combobox = ttk.Combobox(self.wspr_window, values=[
            "one play", "continuously", "1 timeslot out of 2", 
            "1 timeslot out of 3", "1 timeslot out of 4", "1 timeslot out of 5"
        ], width=20)
        self.wspr_frame_combobox.grid(row=4, column=1, padx=5, pady=5)
        self.wspr_frame_combobox.bind("<<ComboboxSelected>>", self.send_wspr_frame_setting)

    def open_fst4w_settings_window(self):
        """打开FST4W设置窗口"""
        self.fst4w_window = tk.Toplevel(self.root)
        self.fst4w_window.title("FST4W设置")

        # FST4W功率设置
        power_label = ttk.Label(self.fst4w_window, text="FST4W功率 (0-60 dBm):")
        power_label.grid(row=0, column=0, padx=5, pady=5)
        self.power_combobox = ttk.Combobox(self.fst4w_window, values=[str(i) for i in range(0, 61)], width=10)
        self.power_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.power_combobox.bind("<<ComboboxSelected>>", self.send_wspr_power_setting)

        # FST4W速度设置
        speed_label = ttk.Label(self.fst4w_window, text="FST4W速度:")
        speed_label.grid(row=1, column=0, padx=5, pady=5)
        self.fst4w_speed_combobox = ttk.Combobox(self.fst4w_window, values=["FST4W-120", "FST4W-300", "FST4W-900", "FST4W-1800"], width=10)
        self.fst4w_speed_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.fst4w_speed_combobox.bind("<<ComboboxSelected>>", self.send_fst4w_speed_setting)

        # FST4W帧设置
        frame_label = ttk.Label(self.fst4w_window, text="FST4W帧设置:")
        frame_label.grid(row=2, column=0, padx=5, pady=5)
        self.fst4w_frame_combobox = ttk.Combobox(self.fst4w_window, values=[
            "one play", "continuously", "1 timeslot out of 2", 
            "1 timeslot out of 3", "1 timeslot out of 4", "1 timeslot out of 5"
        ], width=20)
        self.fst4w_frame_combobox.grid(row=2, column=1, padx=5, pady=5)
        self.fst4w_frame_combobox.bind("<<ComboboxSelected>>", self.send_fst4w_frame_setting)

    def open_jt9_settings_window(self):
        """打开JT9设置窗口"""
        self.jt9_window = tk.Toplevel(self.root)
        self.jt9_window.title("JT9设置")

        # JT9帧设置
        frame_label = ttk.Label(self.jt9_window, text="JT9帧设置:")
        frame_label.grid(row=0, column=0, padx=5, pady=5)
        self.jt9_frame_combobox = ttk.Combobox(self.jt9_window, values=[
            "one play", "continuously", "1 timeslot out of 2", 
            "1 timeslot out of 3", "1 timeslot out of 4", "1 timeslot out of 5"
        ], width=20)
        self.jt9_frame_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.jt9_frame_combobox.bind("<<ComboboxSelected>>", self.send_jt9_frame_setting)

        # JT9速度设置
        speed_label = ttk.Label(self.jt9_window, text="JT9速度:")
        speed_label.grid(row=1, column=0, padx=5, pady=5)
        self.jt9_speed_combobox = ttk.Combobox(self.jt9_window, values=["JT9-1", "JT9-2", "JT9-5", "JT9-10", "JT9-30"], width=10)
        self.jt9_speed_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.jt9_speed_combobox.bind("<<ComboboxSelected>>", self.send_jt9_speed_setting)

    def open_script_remote_settings_window(self):
        """打开Script Remote设置窗口"""
        self.script_remote_window = tk.Toplevel(self.root)
        self.script_remote_window.title("Script Remote设置")

        # SCRIPT帧设置
        frame_label = ttk.Label(self.script_remote_window, text="SCRIPT帧设置:")
        frame_label.grid(row=0, column=0, padx=5, pady=5)
        self.script_frame_combobox = ttk.Combobox(self.script_remote_window, values=["one play", "continuously"], width=15)
        self.script_frame_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.script_frame_combobox.bind("<<ComboboxSelected>>", self.send_script_frame_setting)

        # External REMOTE设置
        remote_label = ttk.Label(self.script_remote_window, text="External REMOTE:")
        remote_label.grid(row=1, column=0, padx=5, pady=5)
        self.remote_combobox = ttk.Combobox(self.script_remote_window, values=[
            "JASON (normal)", "JASON (fast)", "WSQ2", "AFP"
        ], width=15)
        self.remote_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.remote_combobox.bind("<<ComboboxSelected>>", self.send_external_remote_setting)

    def list_ports(self):
        """列出可用的串口"""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        return ports

    def toggle_serial(self):
        """打开或关闭串口"""
        if self.serial_port and self.serial_port.is_open:
            self.close_serial()
        else:
            self.open_serial()

    def open_serial(self):
        """打开串口并进行参数同步"""
        port = self.port_combobox.get()
        baudrate = int(self.baudrate_combobox.get())
        try:
            self.serial_port = serial.Serial(port, baudrate, timeout=1)
            self.log_info(f"串口 {port} 已打开")
            self.toggle_button.config(text="关闭串口")
            self.firmware_button.config(state='normal')  # 启用固件信息按钮
            self.debug_button.config(state='normal')  # 启用调试按钮
            self.set_frequency_button.config(state='normal')  # 启用设置按钮
            self.frequency_entry.config(state='normal')
            self.request_current_settings()  # 连接成功后进行参数同步
            self.start_status_updates()  # 开始状态更新
        except:
            self.log_info(f"打开串口时发生错误")

    def close_serial(self):
        """关闭串口"""
        if self.serial_port and self.serial_port.is_open:
            self.stop_status_updates()  # 停止状态更新
            self.toggle_button.config(text="打开串口")
            self.serial_port.close()
            self.log_info("串口已关闭")
            self.frequency_entry.config(state='disabled')
            self.debug_button.config(state='disabled')  # 禁用调试按钮
            self.set_frequency_button.config(state='disabled')  # 禁用设置按钮
            self.firmware_button.config(state='disabled')  # 禁用固件信息按钮

    def start_status_updates(self):
        """开始定时请求状态信息"""
        self.update_status_ids.append(self.root.after(200, self.request_status_info))  # 每250ms秒请求一次

    def stop_status_updates(self):
        """停止状态更新"""
        for status_id in self.update_status_ids:
            self.root.after_cancel(status_id)
        self.update_status_ids.clear()

    def request_status_info(self):
        """请求电源电压、漏极电流、发射功率、驻波比和发射状态"""
        commands = ['?IB\r', '?ID\r', '?IP\r', '?IS\r', '?B\r']
        for command in commands:
            if self.serial_port and self.serial_port.is_open:
                try:
                    self.serial_port.write(command.encode('utf-8'))
                    response = self.serial_port.readline().decode('utf-8').strip()
                    self.update_status_display(response)
                except Exception as e:
                    self.log_info(f"错误: {str(e)}")
        
        # 继续下次请求
        self.update_status_ids.append(self.root.after(200, self.request_status_info))

    def update_status_display(self, response):
        """更新状态栏显示"""
        if response.startswith('=IB'):
            voltage = int(response[3:]) / 100  # 转换为V
            self.voltage_label.config(text=f"电源电压: {voltage:.2f}V" if voltage != 0 else "电源电压: N/A")
        elif response.startswith('=ID'):
            current = int(response[3:]) / 10  # 转换为A
            self.current_label.config(text=f"漏极电流: {current:.1f}A" if current != 0 else "漏极电流: N/A")
        elif response.startswith('=IP'):
            power = int(response[3:]) / 10  # 转换为W
            self.power_label.config(text=f"发射功率: {power:.1f}W" if power != 0 else "发射功率: N/A")
        elif response.startswith('=IS'):
            swr = int(response[3:]) / 100  # 转换为比率
            if swr != 0:
                self.swr_label.config(text=f"驻波比: {swr:.2f}")
                if swr < 1.5:
                    self.swr_label.config(foreground="green")  # 良好状态
                elif swr < 2.5:
                    self.swr_label.config(foreground="orange")  # 较好状态
                else:
                    self.swr_label.config(foreground="red")  # 差的状态
            else:
                self.swr_label.config(text="驻波比: N/A", foreground="black")  # 没有值时显示为黑色
        elif response.startswith('=B'):  # 更新发射状态
            if response[2] == '1':
                self.transmit_status_label.config(text="状态: 发射", foreground="red")
            else:
                self.transmit_status_label.config(text="状态: 接收", foreground="black")
            
    def log_info(self, message):
        """记录信息到文本框"""
        self.info_text.config(state='normal')
        self.info_text.insert(tk.END, message + "\n")
        self.info_text.config(state='disabled')
        self.info_text.yview(tk.END)

    def send_command(self):
        """发送接收串口命令"""
        text = self.command_entry.get()
        
        if self.serial_port and self.serial_port.is_open:
            try:
                command = f"{text}\r".encode('utf-8')
                self.serial_port.write(command)
                self.log_info(f"发送命令: {text}\r")
            except:
                self.log_info(f"发送命令时发生错误")
            response = self.serial_port.readline().decode('utf-8').strip()
            self.log_info(response)
        else:
            self.log_info("请先连接串口")

    def close_debug_window(self):
        """关闭调试窗口"""
        self.debug_window.destroy()  # 销毁窗口

    def send_firmware_info(self):
        """发送固件信息请求"""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(b"?II\r")
            response = self.serial_port.readline().decode('utf-8').strip()
            self.log_info(f"固件信息: {response}")
    def change_mode(self, event=None):
        """切换下位机模式"""
        value = self.mode_combobox.current()
        if self.serial_port and self.serial_port.is_open:
            command = f"=G{value}\r".encode('utf-8')
            self.serial_port.write(command)
            self.log_info(f"模式已切换: {self.mode_combobox.get()}")

    def set_preamplifier(self, event=None):
        """设置前置放大器"""
        value = self.preamplifier_combobox.current()
        command = f"=A{value}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"前置放大器已设置: {self.preamplifier_combobox.get()}")

    def set_upconverter(self, event=None):
        """设置接收上变频"""
        value = self.upconverter_combobox.current()
        command = f"=C{value}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"接收上变频已设置: {self.upconverter_combobox.get()}")

    def set_cw_mode(self, event=None):
        """设置CW电键模式"""
        value = self.cw_mode_combobox.current()
        command = f"=K{value}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"CW电键模式已设置: {self.cw_mode_combobox.get()}")
            
    def send_cw_identity(self, event=None):
        """设置CW末尾识别发送"""
        value = self.cw_identity_combobox.current()
        command = f"=Y{value}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"发送CW识别: {self.cw_identity_combobox.get()}")

    def set_operation_mode(self, event=None):
        """设置操作模式"""
        value = self.operation_mode_combobox.current()
        command = f"=O{value}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"操作模式已设置: {self.operation_mode_combobox.get()}")

    def set_power(self, event=None):
        """设置发射功率"""
        value = self.power_combobox.current()
        command = f"=P{value}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"发射功率已设置: {self.power_combobox.get()}")

    def send_tx_control_setting(self, event=None):
        """发送TX Control设置指令"""
        index = self.tx_control_combobox.current()
        command = f"=T{index}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"TX Control设置: {self.tx_control_combobox.get()}")

    def update_spare_io_options(self):
        """根据TX136-500板卡安装状态更新SPARE I/O选项"""
        if self.bi_band_var.get() == 1:  # 已安装
            self.spare_io_combobox['values'] = ["136", "500"]
        else:  # 未安装
            self.spare_io_combobox['values'] = ["OFF", "ON"]
        self.spare_io_combobox.current(0)  # 默认选择第一个选项

    # 事件函数
    def send_spare_io_setting(self, event=None):
        """发送SPARE I/O设置指令"""
        index = self.spare_io_combobox.current()
        command = f"=X{index}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"SPARE I/O设置: {self.spare_io_combobox.get()}")

    def send_interval_setting(self, event=None):
        """发送CW\QRSS\DFCW发送间隔设置指令"""
        interval_index = self.interval_combobox.current()
        command = f"=Q{interval_index}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"发送间隔已设置: {self.interval_combobox.get()}")

    def send_jason_interval_setting(self, event=None):
        """发送JASON消息发射间隔设置指令"""
        interval_index = self.jason_interval_combobox.current()
        command = f"=JF{interval_index}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"JASON发射间隔已设置: {self.jason_interval_combobox.get()}")

    def send_jason_speed_setting(self, event=None):
        """发送JASON速度设置指令"""
        speed_index = self.jason_speed_combobox.current() + 2  # 速度选项从2开始
        command = f"=JS{speed_index}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"JASON速度已设置: {self.jason_speed_combobox.get()}")

    def send_opera_frame_setting(self, event=None):
        """发送OPERA Frame设置指令"""
        frame_index = self.opera_frame_combobox.current()
        command = f"=OF{frame_index}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
             self.serial_port.write(command)
             self.log_info(f"OPERA Frame已设置: {self.opera_frame_combobox.get()}")

    def send_opera_speed_setting(self, event=None):
        """发送OPERA速度设置指令"""
        speed_index = self.opera_speed_combobox.current()
        command = f"=OS{speed_index}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
             self.serial_port.write(command)
             self.log_info(f"OPERA速度已设置: {self.opera_speed_combobox.get()}")

    def send_wsq_frame_setting(self, event=None):
        """发送WSQ帧设置指令"""
        wsq_index = self.wsq_frame_combobox.current()
        command = f"=Q{wsq_index}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
             self.serial_port.write(command)
             self.log_info(f"WSQ帧已设置: {self.wsq_frame_combobox.get()}")

    def send_gps_locator_setting(self, event=None):
        """发送GPS定位器选择指令"""
        index = self.gps_locator_combobox.current()
        command = f"=V{index}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
             self.serial_port.write(command)
             self.log_info(f"GPS定位器设置: {self.gps_locator_combobox.get()}")

    def query_gps_value(self):
        """获取GPS定位器值"""
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.write("?W\r".encode('utf-8'))
                response = self.serial_port.readline().decode('utf-8').strip()
                self.gps_value_result.config(text=response)
                self.log_info(f"GPS定位器值: {response}")
            except Exception as e:
                self.log_info(f"错误: {str(e)}")

    def send_wspr_power_setting(self, event=None):
        """发送WSPR功率设置指令"""
        power_value = self.power_combobox.get()
        command = f"=WP{int(power_value):02}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"WSPR功率设置: {power_value} dBm")

    def send_wspr_speed_setting(self, event=None):
        """发送WSPR速度设置指令"""
        index = self.wspr_speed_combobox.current()
        command = f"=WS{index}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"WSPR速度设置: {self.wspr_speed_combobox.get()}")

    def send_wspr_frame_setting(self, event=None):
        """发送WSPR帧设置指令"""
        index = self.wspr_frame_combobox.current()
        command = f"=WF{index}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"WSPR帧设置: {self.wspr_frame_combobox.get()}")

    def send_fst4w_speed_setting(self, event=None):
        """发送FST4W速度设置指令"""
        index = self.fst4w_speed_combobox.current()
        command = f"=WT{index}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"FST4W速度设置: {self.fst4w_speed_combobox.get()}")

    def send_fst4w_frame_setting(self, event=None):
        """发送FST4W帧设置指令"""
        index = self.fst4w_frame_combobox.current()
        command = f"=WG{index}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"FST4W帧设置: {self.fst4w_frame_combobox.get()}")

    def send_jt9_frame_setting(self, event=None):
        """发送JT9帧设置指令"""
        index = self.jt9_frame_combobox.current()
        command = f"=TF{index}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"JT9帧设置: {self.jt9_frame_combobox.get()}")


    def send_jt9_speed_setting(self, event=None):
        """发送JT9速度设置指令"""
        index = self.jt9_speed_combobox.current()
        command = f"=TS{index}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"JT9速度设置: {self.jt9_speed_combobox.get()}")

    def send_script_frame_setting(self, event=None):
        """发送SCRIPT帧设置指令"""
        index = self.script_frame_combobox.current()
        command = f"=SF{index}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"SCRIPT帧设置: {self.script_frame_combobox.get()}")

    def send_external_remote_setting(self, event=None):
        """发送External REMOTE设置指令"""
        index = self.remote_combobox.current()
        command = f"=RS{index}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"External REMOTE设置: {self.remote_combobox.get()}")

    def set_frequency(self):
        """设置频率"""
        try:
            new_freq = int(self.frequency_entry.get())
            if self.serial_port and self.serial_port.is_open:  # 确保串口连接
                if 135700 <= new_freq <= 137800:
                    command = f"=F{new_freq:06d}\r".encode('utf-8')
                    self.serial_port.write(command)
                    self.frequency = new_freq
                    self.current_frequency_value.set(f"{self.frequency} Hz")
                    self.log_info(f"频率已设置: {self.frequency} Hz")
                else:
                    self.log_info("频率超出范围")
            else:
                self.log_info("请先连接串口")
        except ValueError:
            self.log_info("请输入有效的频率")


    def send_callsign(self):
        """设置呼号"""
        text = self.callsign_entry.get()
        command = f"=Z{text}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"发送呼号: {text}")

    def send_cw_beacon(self):
        """设置CW信标内容"""
        text = self.cw_beacon_entry.get()
        command = f"=E{text}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"发送CW信标文本: {text}")

    def send_beacon_text(self):
        """设置信标内容"""
        text = self.beacon_text_entry.get()
        command = f"=H{text}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"发送信标文本: {text}")

    def send_grid(self):
        """设置网格"""
        text = self.grid_entry.get()
        command = f"=L{text}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"发送网格坐标: {text}")
            
    def send_dot_time(self, event=None):
        """发送点时间设置指令"""
        value = int(self.dot_time_combobox.get())
        command = f"=D{value}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"点时间已设置: {value}")

    def send_dfcw_dash_shift(self, event=None):
        """发送DFCW频移设置指令"""
        value = float(self.dfcw_shift_combobox.get()) * 10  # 乘以10
        command = f"=R{int(value)}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"发送频率偏移: {value / 10}")

    def send_cw_speed(self, event=None):
        """发送CW速度"""
        value = int(self.cw_speed_combobox.get()) * 10  # 从下拉菜单获取值并乘以10
        command = f"=S{value}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"发送CW速度: {value // 10}")

    def send_script_text(self):
        text = self.script_text_entry.get()
        command = f"=U{text}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"发送自动脚本文本: {text}")

    def send_time_sync(self):
        """读取当前系统时间并发送到下位机"""
        current_time = time.localtime()
        total_seconds = current_time.tm_min * 60 + current_time.tm_sec
        if 1 <= total_seconds <= 3599:
            command = f"=N{total_seconds:04d}\r".encode('utf-8')
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.write(command)
                self.log_info(f"时间同步已发送: {total_seconds // 60:02d}:{total_seconds % 60:02d}")
        else:
            self.log_info("时间超出范围")

    def send_input_info(self):
        """发送输入框内的信息"""
        text = self.input_entry.get()
        if all(ord(char) < 128 for char in text):  # 确保输入的都是ASCII字符
            command = f"=M{text}\r=BT\r".encode('utf-8')
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.write(command)
                self.log_info(f"发送输入信息: {text}")
        else:
            self.log_info("输入信息必须为ASCII字符")

    def send_onboard_info(self):
        """发送机载信息"""
        command = b"=B1\r"
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info("发送机载信息")

    def stop_transmission(self):
        """停止发射"""
        command = b"=B0\r"
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info("停止发射")

    def request_current_settings(self):
        """询问当前设置并更新UI"""
        queries = ['?G\r', '?A\r', '?C\r', '?K\r', '?O\r', '?P\r', '?F\r', '?Z\r', '?E\r', '?H\r', '?L\r', '?D\r', '?R\r', '?S\r', '?U\r', '?Y\r']
        for query in queries:
            if self.serial_port and self.serial_port.is_open:
                try:
                    self.serial_port.write(query.encode('utf-8'))
                    response = self.serial_port.readline().decode('utf-8').strip()
                    self.update_settings(response)
                except Exception as e:
                    self.log_info(f"错误: {str(e)}")

    def update_settings(self, response):
        """更新UI中的设置值"""
        if response.startswith('=G'):
            mode_index = int(response[2])
            self.mode_combobox.current(mode_index)

        elif response.startswith('=A'):
            preamplifier_index = int(response[2])
            self.preamplifier_combobox.current(preamplifier_index)

        elif response.startswith('=C'):
            upconverter_index = int(response[2])
            self.upconverter_combobox.current(upconverter_index)

        elif response.startswith('=K'):
            cw_mode_index = int(response[2])
            self.cw_mode_combobox.current(cw_mode_index)

        elif response.startswith('=O'):
            operation_mode_index = int(response[2])
            self.operation_mode_combobox.current(operation_mode_index)

        elif response.startswith('=P'):
            power_index = int(response[2])
            self.power_combobox.current(power_index)

        elif response.startswith('=F'):
            frequency_value = int(response[2:])
            self.frequency = frequency_value
            self.current_frequency_value.set(f"{self.frequency} Hz")

        elif response.startswith('=Z'):
            callsign = response[2:]
            self.callsign_entry.delete(0, tk.END)
            self.callsign_entry.insert(0, callsign)

        elif response.startswith('=E'):
            cw_beacon_text = response[2:]
            self.cw_beacon_entry.delete(0, tk.END)
            self.cw_beacon_entry.insert(0, cw_beacon_text)

        elif response.startswith('=H'):
            beacon_text = response[2:]
            self.beacon_text_entry.delete(0, tk.END)
            self.beacon_text_entry.insert(0, beacon_text)

        elif response.startswith('=L'):
            grid = response[2:]
            self.grid_entry.delete(0, tk.END)
            self.grid_entry.insert(0, grid)

        elif response.startswith('=D'):
            dot_time = int(response[2:])
            self.dot_time_entry.delete(0, tk.END)
            self.dot_time_entry.insert(0, dot_time)

        elif response.startswith('=R'):
            dfcw_shift = int(response[2:])
            self.dfcw_shift_entry.delete(0, tk.END)
            self.dfcw_shift_entry.insert(0, str(dfcw_shift / 10))

        elif response.startswith('=S'):
            cw_speed = int(response[2:])
            self.cw_speed_entry.delete(0, tk.END)
            self.cw_speed_entry.insert(0, str(cw_speed // 10))

        elif response.startswith('=U'):
            script_text = response[2:]
            self.script_text_entry.delete(0, tk.END)
            self.script_text_entry.insert(0, script_text)

        elif response.startswith('=Y'):
            cw_identity_value = int(response[2])
            self.cw_identity_combobox.current(cw_identity_value)
        
if __name__ == "__main__":
    root = tk.Tk()
    app = SerialControlApp(root)
    root.mainloop()
