import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedStyle
import serial
import serial.tools.list_ports
import time

class SerialControlApp:
    #============================================================
    #                        主窗口区域
    #============================================================
    def __init__(self, root):
        self.root = root
        self.root.title("Juma TX136控制程序 BH3PTS 20241102")
        self.root.resizable(False, False)
        self.serial_port = None
        self.frequency = 136000  # 初始频率
        self.update_status_id = None #设置发射状态
        

        
        # ----------------------频率设置区域----------------------
        
        self.frequency_frame = ttk.LabelFrame(root, text="频率设置")
        self.frequency_frame.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')
        
        self.current_frequency_value = tk.StringVar(value=f"{self.frequency}")
        self.current_frequency_display = ttk.Label(self.frequency_frame, textvariable=self.current_frequency_value, font=("Arial", 36), anchor='se')
        self.current_frequency_display.grid(row=0, rowspan=2, column=0, columnspan=2, padx=5, pady=5, sticky='nsew')
        
        self.current_frequencyHz_label = ttk.Label(self.frequency_frame, text="Hz", font=("Arial", 24), anchor='sw')
        self.current_frequencyHz_label.grid(row=0, rowspan=2, column=2, padx=5, pady=5, sticky='sew')
        
        self.decrease_100_button = ttk.Button(self.frequency_frame, text="-100 Hz", command=lambda: self.adjust_frequency(-100), state='disabled')
        self.decrease_100_button.grid(row=2, column=0, padx=5, pady=5)

        self.decrease_1_button = ttk.Button(self.frequency_frame, text="-1 Hz", command=lambda: self.adjust_frequency(-1), state='disabled')
        self.decrease_1_button.grid(row=2, column=1, padx=5, pady=5)

        self.increase_1_button = ttk.Button(self.frequency_frame, text="+1 Hz", command=lambda: self.adjust_frequency(1), state='disabled')
        self.increase_1_button.grid(row=2, column=2, padx=5, pady=5)

        self.increase_100_button = ttk.Button(self.frequency_frame, text="+100 Hz", command=lambda: self.adjust_frequency(100), state='disabled')
        self.increase_100_button.grid(row=2, column=3, padx=5, pady=5)
        
        self.frequency_entry = ttk.Entry(self.frequency_frame, width=11)
        self.frequency_entry.grid(row=0, column=3, columnspan=2, padx=5, pady=5)
        self.frequency_entry.config(state='disabled')
        self.frequency_entry.bind("<Return>", lambda event: self.set_frequency())
        
        self.set_frequency_button = ttk.Button(self.frequency_frame, text="频率设置", command=self.set_frequency, state='disabled')
        self.set_frequency_button.grid(row=1, column=3, padx=5, pady=5)
       
        # ----------------------串口设置区域----------------------

        self.port_frame = ttk.LabelFrame(root, text="串口设置")
        self.port_frame.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')

        self.toggle_button = ttk.Button(self.port_frame, text="打开串口", command=self.toggle_serial)
        self.toggle_button.grid(row=0, column=0, padx=5, pady=5)

        self.port_combobox = ttk.Combobox(self.port_frame, values=self.list_ports(), width=8)
        self.port_combobox.grid(row=0, column=1, padx=5, pady=5)
        
        # 准备在这里放点东西 rowspan=2

        self.baudrate_label = ttk.Label(self.port_frame, text="波特率: ")
        self.baudrate_label.grid(row=1, column=0, padx=5, pady=5)

        self.baudrate_combobox = ttk.Combobox(self.port_frame, values=[1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200], width=8)
        self.baudrate_combobox.set(9600)
        self.baudrate_combobox.grid(row=1, column=1, padx=5, pady=5)

        self.sync_button = ttk.Button(self.port_frame, text="参数同步", command=self.request_current_settings, state='disabled')
        self.sync_button.grid(row=2, column=0, padx=5, pady=5)


        self.firmware_button = ttk.Button(self.port_frame, text="固件信息",command=self.send_firmware_info, state='disabled')
        self.firmware_button.grid(row=2, column=1, padx=5, pady=5)

        # ----------------------基础设置区域----------------------
        
        self.control_frame = ttk.LabelFrame(root, text="电台控制")
        self.control_frame.grid(row=1, rowspan=2, column=0, padx=5, pady=5, sticky='nsew')        
        
        # 模式切换
        self.mode_label = ttk.Label(self.control_frame, text="模式切换:")
        self.mode_label.grid(row=0, column=0, padx=5, pady=5)

        self.mode_combobox = ttk.Combobox(self.control_frame, values=["CW", "QRSS", "DFCW", "JASON", "WSQ2", "OPERA", "WSPR", "FST4W", "JT9", "SCRIPT", "REMOTE"], width=8)
        self.mode_combobox.set("CW")
        self.mode_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.mode_combobox.bind("<<ComboboxSelected>>", self.change_mode)
        
        # 操作模式设置
        self.operation_mode_label = ttk.Label(self.control_frame, text="操作模式:")
        self.operation_mode_label.grid(row=1, column=0, padx=5, pady=5)

        self.operation_mode_combobox = ttk.Combobox(self.control_frame, values=["Stand By", "Operation", "Tune"], width=8)
        self.operation_mode_combobox.set("Stand By")
        self.operation_mode_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.operation_mode_combobox.bind("<<ComboboxSelected>>", self.set_operation_mode)
        
        # 发射功率设置
        self.power_label = ttk.Label(self.control_frame, text="发射功率:")
        self.power_label.grid(row=2, column=0, padx=5, pady=5)

        self.power_combobox = ttk.Combobox(self.control_frame, values=["MIN", "LOW", "HIGH", "MAX"], width=8)
        self.power_combobox.set("MIN")
        self.power_combobox.grid(row=2, column=1, padx=5, pady=5)
        self.power_combobox.bind("<<ComboboxSelected>>", self.set_power)
        
        # 时间同步
        self.time_sync_button = ttk.Button(self.control_frame, text="时间同步", command=self.send_time_sync, state='disabled')
        self.time_sync_button.grid(row=3, column=0, padx=5, pady=5)
        
        # 进阶控制按钮
        self.advanced_control_button = ttk.Button(self.control_frame, text="打开进阶设置", command=self.open_advanced_control_window)
        self.advanced_control_button.grid(row=3, column=1, padx=5, pady=5)
        
        
        # ----------------------信息区与调试区域----------------------
        
        self.info_text = tk.Text(root, height=6, width=50, state='disabled')
        self.info_text.grid(row=1, column=1, padx=5, pady=5)

        self.scrollbar = ttk.Scrollbar(root, command=self.info_text.yview)
        # 输入栏
        self.debug_frame = ttk.LabelFrame(root, text="串口指令调试 无需输入CR转义符")
        self.debug_frame.grid(row=2, column=1, padx=5, pady=5, sticky='nsew')
        
        self.command_entry = ttk.Entry(self.debug_frame, width=38)
        self.command_entry.grid(row=0, column=0, padx=5, pady=5)
        self.command_entry.bind("<Return>", lambda event: self.send_command())
        
        send_button = ttk.Button(self.debug_frame, text="发送", command=self.send_command)
        send_button.grid(row=0, column=1, padx=5, pady=5)
        
        # ----------------------信息输入区域----------------------
        
        self.input_frame = ttk.LabelFrame(root, text="自定义信息发射(仅支持ASCII）")
        self.input_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky='nsew')

        self.input_entry = ttk.Entry(self.input_frame, width=39)
        self.input_entry.grid(row=0, columnspan=4, padx=10, pady=10)
        self.input_entry.bind("<Return>", lambda event: self.send_input_info())

        # 按钮: 发送输入信息, 开始发射, 停止发射
        self.send_input_button = ttk.Button(self.input_frame, text="发送输入信息", command=self.send_input_info)
        self.send_input_button.grid(row=0, column=4, padx=5, pady=5)

        self.send_onboard_button = ttk.Button(self.input_frame, text="发送机载信标", command=self.send_onboard_info)
        self.send_onboard_button.grid(row=0, column=5, padx=5, pady=5)

        self.stop_transmission_button = ttk.Button(self.input_frame, text="停止发射", command=self.stop_transmission)
        self.stop_transmission_button.grid(row=0, column=6, padx=5, pady=5)
        
        # ----------------------状态栏----------------------
        
        self.status_frame = ttk.Frame(root)
        self.status_frame.grid(row=4, column=0, columnspan=2, pady=5, sticky='ew')  # 修改行号为4以放在底部

        self.voltage_label = ttk.Label(self.status_frame, text="电源电压: N/A", width=14)
        self.voltage_label.grid(row=0, column=0, padx=10, sticky='nsew')

        self.current_label = ttk.Label(self.status_frame, text="漏极电流: N/A", width=14)
        self.current_label.grid(row=0, column=1, padx=10, sticky='nsew')

        self.power_label = ttk.Label(self.status_frame, text="发射功率: N/A", width=14)
        self.power_label.grid(row=0, column=2, padx=10, sticky='nsew')

        self.swr_label = ttk.Label(self.status_frame, text="驻波比: N/A", width=14)
        self.swr_label.grid(row=0, column=3, padx=10, sticky='nsew')

        self.transmit_status_label = ttk.Label(self.status_frame, text="状态: N/A", width=14)
        self.transmit_status_label.grid(row=0, column=4, padx=10, sticky='nsew')
        

    #============================================================
    #                        进阶窗口区域
    #============================================================    

    def open_advanced_control_window(self):
        """打开进阶控制窗口"""
        self.advanced_control_window = tk.Toplevel(self.root)
        self.advanced_control_window.title("进阶控制")
        self.advanced_control_window.resizable(False, False)

        # ----------------------接收设置----------------------
        self.receive_settings_frame = ttk.LabelFrame(self.advanced_control_window, text="接收设置")
        self.receive_settings_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        # 前置放大器设置
        self.preamplifier_label = ttk.Label(self.receive_settings_frame, text="前置放大器:")
        self.preamplifier_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.preamplifier_combobox = ttk.Combobox(self.receive_settings_frame, values=["OFF", "10 dB", "20 dB"], width=9)
        self.preamplifier_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.preamplifier_combobox.bind("<<ComboboxSelected>>", self.set_preamplifier)

        # 接收上变频设置
        self.upconverter_label = ttk.Label(self.receive_settings_frame, text="接收上变频:")
        self.upconverter_label.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        self.upconverter_combobox = ttk.Combobox(self.receive_settings_frame, values=["OFF", "ON"], width=9)
        self.upconverter_combobox.grid(row=0, column=3, padx=5, pady=5)
        self.upconverter_combobox.bind("<<ComboboxSelected>>", self.set_upconverter)
        
        # ----------------------设备关键设置----------------------
        self.tx_control_frame = ttk.LabelFrame(self.advanced_control_window, text="设备关键设置")
        self.tx_control_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        # TX Control设置
        self.tx_control_label = ttk.Label(self.tx_control_frame, text="TX控制方式:")
        self.tx_control_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.tx_control_combobox = ttk.Combobox(self.tx_control_frame, values=["Auto", "MOX", "RTS 悬空会发射"], width=10)
        self.tx_control_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.tx_control_combobox.bind("<<ComboboxSelected>>", self.send_tx_control_setting)

        # SPARE I/O设置
        self.spare_io_label = ttk.Label(self.tx_control_frame, text="SPARE I/O:")
        self.spare_io_label.grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.spare_io_combobox = ttk.Combobox(self.tx_control_frame, values=["OFF", "ON"], width=10)
        self.spare_io_combobox.grid(row=1, column=3, padx=5, pady=5)
        self.spare_io_combobox.bind("<<ComboboxSelected>>", self.send_spare_io_setting)

        # 二选一设置
        self.bi_band_label = ttk.Label(self.tx_control_frame, text="TX136-500双段板卡是否安装:")
        self.bi_band_label.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        self.bi_band_var = tk.IntVar()
        self.bi_band_off_radio = ttk.Radiobutton(self.tx_control_frame, text="已安装", variable=self.bi_band_var, value=1, command=self.update_spare_io_options)
        self.bi_band_off_radio.grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.bi_band_on_radio = ttk.Radiobutton(self.tx_control_frame, text="未安装", variable=self.bi_band_var, value=0, command=self.update_spare_io_options)
        self.bi_band_on_radio.grid(row=2, column=3, padx=5, pady=5, sticky="w")
        self.update_spare_io_options()
        
        # CW识别发送
        self.cw_identity_label = ttk.Label(self.tx_control_frame, text="末尾识别CW码发送（除了CW都有）：")
        self.cw_identity_label.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        self.cw_identity_combobox = ttk.Combobox(self.tx_control_frame, values=["OFF", "12 wpm", "24 wpm"], width=10)
        self.cw_identity_combobox.grid(row=3, column=2, padx=5, pady=5)
        self.cw_identity_combobox.bind("<<ComboboxSelected>>", self.send_cw_identity)

        # 呼号输入
        self.callsign_button = ttk.Button(self.tx_control_frame, text="上传呼号", command=self.send_callsign)
        self.callsign_button.grid(row=0, column=0, padx=5, pady=5)
        self.callsign_entry = ttk.Entry(self.tx_control_frame, width=10)
        self.callsign_entry.grid(row=0, column=1, padx=5, pady=5)
        self.callsign_entry.bind("<Return>", lambda event: self.send_callsign())  # 绑定回车事件

        # 网格坐标输入
        self.grid_button = ttk.Button(self.tx_control_frame, text="上传网格坐标", command=self.send_grid)
        self.grid_button.grid(row=0, column=2, padx=5, pady=5)
        self.grid_entry = ttk.Entry(self.tx_control_frame, width=10)
        self.grid_entry.grid(row=0, column=3, padx=5, pady=5)
        self.grid_entry.bind("<Return>", lambda event: self.send_grid())  # 绑定回车事件
        
        # ----------------------CW/QRSS/DFCW设置----------------------
        self.cw_qrss_dfcw_frame = ttk.LabelFrame(self.advanced_control_window, text="CW/QRSS/DFCW设置")
        self.cw_qrss_dfcw_frame.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")

        # CW电键模式设置
        self.cw_mode_label = ttk.Label(self.cw_qrss_dfcw_frame, text="CW电键模式:")
        self.cw_mode_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.cw_mode_combobox = ttk.Combobox(self.cw_qrss_dfcw_frame, values=["Dot priority", "Iambic A", "Iambic B", "Straight", "Beacon"], width=10)
        self.cw_mode_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.cw_mode_combobox.bind("<<ComboboxSelected>>", self.set_cw_mode)

        # CW WPM输入
        self.cw_speed_label = ttk.Label(self.cw_qrss_dfcw_frame, text="CW WPM码率:")
        self.cw_speed_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.cw_speed_combobox = ttk.Combobox(self.cw_qrss_dfcw_frame, values=[str(i) for i in range(1, 51)], width=10)
        self.cw_speed_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.cw_speed_combobox.bind("<<ComboboxSelected>>", self.send_cw_speed)

        # 点时间设置
        self.dot_time_label = ttk.Label(self.cw_qrss_dfcw_frame, text="点时间设置:")
        self.dot_time_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.dot_time_combobox = ttk.Combobox(self.cw_qrss_dfcw_frame, values=[str(i) for i in range(1, 121)], width=10)
        self.dot_time_combobox.grid(row=2, column=1, padx=5, pady=5)
        self.dot_time_combobox.bind("<<ComboboxSelected>>", self.send_dot_time)  # 绑定选择事件

        # DFCW频移设置
        self.dfcw_shift_label = ttk.Label(self.cw_qrss_dfcw_frame, text="DFCW频移设置:")
        self.dfcw_shift_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.dfcw_shift_combobox = ttk.Combobox(self.cw_qrss_dfcw_frame, values=[f"{i/10:.1f}" for i in range(1, 51)], width=10)  # 0.1 到 5.0
        self.dfcw_shift_combobox.grid(row=3, column=1, padx=5, pady=5)
        self.dfcw_shift_combobox.bind("<<ComboboxSelected>>", self.send_dfcw_dash_shift)  # 绑定选择事件

        # 发送间隔设置
        self.interval_label = ttk.Label(self.cw_qrss_dfcw_frame, text="发送帧设置:")
        self.interval_label.grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.interval_combobox = ttk.Combobox(self.cw_qrss_dfcw_frame, values=[
            "单次发射", "连续发射", "间隔一次", 
            "间隔两次", "间隔三次", "间隔四次"
        ], width=10)
        self.interval_combobox.grid(row=4, column=1, padx=5, pady=5)
        self.interval_combobox.bind("<<ComboboxSelected>>", self.send_interval_setting)
        
        # ----------------------JASON/OPERA/WSQ设置----------------------
        self.jason_opera_wsq_frame = ttk.LabelFrame(self.advanced_control_window, text="JASON/OPERA/WSQ设置")
        self.jason_opera_wsq_frame.grid(row=2, column=1, padx=5, pady=5, sticky="nsew")

        # JASON发射帧设置
        self.jason_frame_label = ttk.Label(self.jason_opera_wsq_frame, text="Jason发射帧设置:")
        self.jason_frame_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.jason_interval_combobox = ttk.Combobox(self.jason_opera_wsq_frame, values=[
            "单次发射", "连续发射", "间隔一次", 
            "间隔两次", "间隔三次", "间隔四次"
        ], width=10)
        self.jason_interval_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.jason_interval_combobox.bind("<<ComboboxSelected>>", self.send_jason_interval_setting)

        # JASON速度设置
        self.jason_speed_label = ttk.Label(self.jason_opera_wsq_frame, text="JASON速度设置:")
        self.jason_speed_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.jason_speed_combobox = ttk.Combobox(self.jason_opera_wsq_frame, values=[
            "Normal", "Normal turbo", "Fast", "Fast turbo"
        ], width=10)
        self.jason_speed_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.jason_speed_combobox.bind("<<ComboboxSelected>>", self.send_jason_speed_setting)

        # WSQ帧设置
        self.wsq_frame_label = ttk.Label(self.jason_opera_wsq_frame, text="WSQ帧设置:")
        self.wsq_frame_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.wsq_frame_combobox = ttk.Combobox(self.jason_opera_wsq_frame, values=[
            "单次发射", "连续发射", "间隔一次", 
            "间隔两次", "间隔三次", "间隔四次"
        ], width=10)
        self.wsq_frame_combobox.grid(row=2, column=1, padx=5, pady=5)
        self.wsq_frame_combobox.bind("<<ComboboxSelected>>", self.send_wsq_frame_setting)

        # OPERA frame设置
        self.opera_frame_label = ttk.Label(self.jason_opera_wsq_frame, text="OPERA发射帧设置:")
        self.opera_frame_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.opera_frame_combobox = ttk.Combobox(self.jason_opera_wsq_frame, values=[
            "单次发射", "连续发射", "间隔一次", 
            "间隔两次", "间隔三次", "间隔四次"
        ], width=10)
        self.opera_frame_combobox.grid(row=3, column=1, padx=5, pady=5)
        self.opera_frame_combobox.bind("<<ComboboxSelected>>", self.send_opera_frame_setting)

        # OPERA速度设置
        self.opera_speed_label = ttk.Label(self.jason_opera_wsq_frame, text="OPERA速度设置:")
        self.opera_speed_label.grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.opera_speed_combobox = ttk.Combobox(self.jason_opera_wsq_frame, values=[
            "OPERA 2", "OPERA 4", "OPERA 8", "OPERA 16", "OPERA 32", "OPERA 65"
        ], width=10)
        self.opera_speed_combobox.grid(row=4, column=1, padx=5, pady=5)
        self.opera_speed_combobox.bind("<<ComboboxSelected>>", self.send_opera_speed_setting)

        # ----------------------WSPR/FST4W/JT9设置----------------------
        self.wspr_fst4w_jt9_frame = ttk.LabelFrame(self.advanced_control_window, text="WSPR/FST4W/JT9设置")
        self.wspr_fst4w_jt9_frame.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        # WSPR设置

        # GPS定位器开关
        self.gps_locator_label = ttk.Label(self.wspr_fst4w_jt9_frame, text="GPS定位器开关:")
        self.gps_locator_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.gps_locator_combobox = ttk.Combobox(self.wspr_fst4w_jt9_frame, values=["OFF", "ON"], width=10)
        self.gps_locator_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.gps_locator_combobox.bind("<<ComboboxSelected>>", self.send_gps_locator_setting)

        # GPS定位器值
        self.gps_value_button = ttk.Button(self.wspr_fst4w_jt9_frame, text="获取GPS值", command=self.query_gps_value)
        self.gps_value_button.grid(row=0, column=2, padx=5, pady=5)
        self.gps_value_result = ttk.Label(self.wspr_fst4w_jt9_frame, text="N/A", relief="sunken", width=10)
        self.gps_value_result.grid(row=0, column=3, padx=5, pady=5)

        # WSPR功率设置
        self.wspr_power_label = ttk.Label(self.wspr_fst4w_jt9_frame, text="功率标定:   功率最高档Max的实际功率，单位dbm")
        self.wspr_power_label.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="w")
        self.wspr_power_combobox = ttk.Combobox(self.wspr_fst4w_jt9_frame, values=[str(i) for i in range(0, 61)], width=10)
        self.wspr_power_combobox.grid(row=1, column=3, padx=5, pady=5)
        self.wspr_power_combobox.bind("<<ComboboxSelected>>", self.send_wspr_power_setting)

        # WSPR速度设置
        self.wspr_speed_label = ttk.Label(self.wspr_fst4w_jt9_frame, text="WSPR速度:")
        self.wspr_speed_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.wspr_speed_combobox = ttk.Combobox(self.wspr_fst4w_jt9_frame, values=["WSPR-2", "WSPR-15"], width=10)
        self.wspr_speed_combobox.grid(row=2, column=1, padx=5, pady=5)
        self.wspr_speed_combobox.bind("<<ComboboxSelected>>", self.send_wspr_speed_setting)

        # WSPR帧设置
        self.wspr_frame_label = ttk.Label(self.wspr_fst4w_jt9_frame, text="WSPR帧设置:")
        self.wspr_frame_label.grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.wspr_frame_combobox = ttk.Combobox(self.wspr_fst4w_jt9_frame, values=[
            "单次发射", "连续发射", "间隔一次", 
            "间隔两次", "间隔三次", "间隔四次"
        ], width=10)
        self.wspr_frame_combobox.grid(row=2, column=3, padx=5, pady=5)
        self.wspr_frame_combobox.bind("<<ComboboxSelected>>", self.send_wspr_frame_setting)

        # FST4W设置

        # FST4W速度设置
        self.fst4w_speed_label = ttk.Label(self.wspr_fst4w_jt9_frame, text="FST4W速度:")
        self.fst4w_speed_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.fst4w_speed_combobox = ttk.Combobox(self.wspr_fst4w_jt9_frame, values=["FST4W-120", "FST4W-300", "FST4W-900", "FST4W-1800"], width=10)
        self.fst4w_speed_combobox.grid(row=3, column=1, padx=5, pady=5)
        self.fst4w_speed_combobox.bind("<<ComboboxSelected>>", self.send_fst4w_speed_setting)

        # FST4W帧设置
        self.fst4w_frame_label = ttk.Label(self.wspr_fst4w_jt9_frame, text="FST4W帧设置:")
        self.fst4w_frame_label.grid(row=3, column=2, padx=2, pady=5, sticky="w")
        self.fst4w_frame_combobox = ttk.Combobox(self.wspr_fst4w_jt9_frame, values=[
            "单次发射", "连续发射", "间隔一次", 
            "间隔两次", "间隔三次", "间隔四次"
        ], width=10)
        self.fst4w_frame_combobox.grid(row=3, column=3, padx=5, pady=5)
        self.fst4w_frame_combobox.bind("<<ComboboxSelected>>", self.send_fst4w_frame_setting)

        # JT9设置

        # JT9速度设置
        self.jt9_speed_label = ttk.Label(self.wspr_fst4w_jt9_frame, text="JT9速度:")
        self.jt9_speed_label.grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.jt9_speed_combobox = ttk.Combobox(self.wspr_fst4w_jt9_frame, values=["JT9-1", "JT9-2", "JT9-5", "JT9-10", "JT9-30"], width=10)
        self.jt9_speed_combobox.grid(row=4, column=1, padx=5, pady=5)
        self.jt9_speed_combobox.bind("<<ComboboxSelected>>", self.send_jt9_speed_setting)
        
        # JT9帧设置
        self.jt9_frame_label = ttk.Label(self.wspr_fst4w_jt9_frame, text="JT9帧设置:")
        self.jt9_frame_label.grid(row=4, column=2, padx=5, pady=5, sticky="w")
        self.jt9_frame_combobox = ttk.Combobox(self.wspr_fst4w_jt9_frame, values=[
            "单次发射", "连续发射", "间隔一次", 
            "间隔两次", "间隔三次", "间隔四次"
        ], width=10)
        self.jt9_frame_combobox.grid(row=4, column=3, padx=5, pady=5)
        self.jt9_frame_combobox.bind("<<ComboboxSelected>>", self.send_jt9_frame_setting)


        # ----------------------无标签Frame设置----------------------
        self.script_frame = ttk.Frame(self.advanced_control_window)
        self.script_frame.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        # SCRIPT帧设置
        self.script_frame_label = ttk.Label(self.script_frame, text="SCRIPT帧设置:")
        self.script_frame_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.script_frame_combobox = ttk.Combobox(self.script_frame, values=["单次发射", "连续发射", "间隔一次", 
            "间隔两次", "间隔三次", "间隔四次"], width=10)
        self.script_frame_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.script_frame_combobox.bind("<<ComboboxSelected>>", self.send_script_frame_setting)

        #创建同步按钮并绑定事件
        self.sync_button = tk.Button(self.script_frame, text="进阶参数同步", command=self.sync_settings)
        self.sync_button.grid(row=0, column=3, padx=5, pady=5)

        # External REMOTE设置
        self.remote_label = ttk.Label(self.script_frame, text="External REMOTE:")
        self.remote_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.remote_combobox = ttk.Combobox(self.script_frame, values=["OFF", "ON"], width=10)
        self.remote_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.remote_combobox.bind("<<ComboboxSelected>>", self.send_external_remote_setting)

        # CW信标设置
        self.cw_beacon_label = ttk.Label(self.script_frame, text="CW信标设置:")
        self.cw_beacon_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.cw_beacon_entry = ttk.Entry(self.script_frame, width=24)
        self.cw_beacon_entry.grid(row=2, column=1, columnspan=2, padx=5, pady=5)
        self.cw_beacon_button = ttk.Button(self.script_frame, text="上传CW信标", command=self.send_cw_beacon)
        self.cw_beacon_button.grid(row=2, column=3, padx=5, pady=5)

        # 信标文本设置
        self.beacon_text_label = ttk.Label(self.script_frame, text="信标文本设置:")
        self.beacon_text_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.beacon_text_entry = ttk.Entry(self.script_frame, width=24)
        self.beacon_text_entry.grid(row=3, column=1, columnspan=2, padx=5, pady=5)
        self.beacon_text_button = ttk.Button(self.script_frame, text="上传信标文本", command=self.send_beacon_text)
        self.beacon_text_button.grid(row=3, column=3, padx=5, pady=5)

        # 自动脚本文本设置
        self.script_text_label = ttk.Label(self.script_frame, text="自动脚本文本设置:")
        self.script_text_label.grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.script_text_entry = ttk.Entry(self.script_frame, width=24)
        self.script_text_entry.grid(row=4, column=1, columnspan=2, padx=5, pady=5)
        self.script_text_button = ttk.Button(self.script_frame, text="上传自动脚本", command=self.send_script_text)
        self.script_text_button.grid(row=4, column=3, padx=5, pady=5)

        # 在窗口打开后进行同步设置
        self.advanced_control_window.after(100, self.sync_settings)
    
    #============================================================
    #                        基础事件函数
    #============================================================
    
    # ----------------------频率设置----------------------
    
    def set_frequency(self):
        """设置频率"""
        try:
            new_freq = int(self.frequency_entry.get())
            if self.serial_port and self.serial_port.is_open:  # 确保串口连接
                if 135700 <= new_freq <= 137800:
                    command = f"=F{new_freq:06d}\r".encode('utf-8')
                    self.serial_port.write(command)
                    self.frequency = new_freq
                    self.current_frequency_value.set(f"{self.frequency}")
                    self.log_info(f"频率已设置: {self.frequency} Hz")
                else:
                    self.log_info("频率超出范围")
        except ValueError:
            self.log_info("请输入有效的频率")

    def adjust_frequency(self, increment):
        """按钮调整频率（数值决定加减范围）"""
        new_freq = self.frequency + increment
        if 135700 <= new_freq <= 137800:
            self.frequency = new_freq
            self.current_frequency_value.set(f"{self.frequency}")
            if self.serial_port and self.serial_port.is_open:  # 确保串口连接
                command = f"=F{self.frequency:06d}\r".encode('utf-8')
                self.serial_port.write(command)
        
    # ----------------------串口设置----------------------
    
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
            # 在此设置更高的超时来防止程序卡死
            self.serial_port = serial.Serial(port, baudrate, timeout=1)
            
            # 如果串口打开成功，执行后续操作
            self.log_info(f"串口 {port} 已打开")
            self.toggle_button.config(text="关闭串口")
            self.firmware_button.config(state='normal')  # 启用固件信息按钮
            self.set_frequency_button.config(state='normal')  # 启用频率设置按钮
            self.decrease_100_button.config(state='normal')  # 启用-100按钮
            self.decrease_1_button.config(state='normal')  # 启用-1按钮
            self.increase_1_button.config(state='normal')  # 启用+1按钮
            self.increase_100_button.config(state='normal')  # 启用+100按钮
            self.time_sync_button.config(state='normal')  # 启用时间同步按钮
            self.sync_button.config(state='normal')  # 启用参数同步按钮
            self.frequency_entry.config(state='normal')
            
            self.request_current_settings()  # 连接成功后进行参数同步
            self.start_status_updates()  # 开始状态更新

        except serial.SerialException as e: # 捕获串口异常
            self.log_info(f"打开串口时发生错误: {e}")
            self.toggle_button.config(text="打开串口")  # 如果打开失败，保持按钮文字不变
            self.show_error_message(f"无法打开串口 {port}，请检查波特率设置或设备状态。")
        
        except ValueError as e:
            # 捕获波特率格式错误
            self.log_info(f"波特率设置错误: {e}")
            self.show_error_message(f"波特率设置无效: {baudrate}. 请确保选择有效的波特率。")

        except Exception as e:
            # 捕获其他未知错误
            self.log_info(f"未知错误: {e}")
            self.show_error_message("发生未知错误，请稍后重试。")

    def close_serial(self):
        """关闭串口"""
        if self.serial_port and self.serial_port.is_open:
            self.stop_status_updates()  # 停止状态更新
            self.toggle_button.config(text="打开串口")
            self.serial_port.close()
            self.log_info("串口已关闭")
            self.frequency_entry.config(state='disabled')
            self.decrease_100_button.config(state='disabled')  # 禁用-100按钮
            self.decrease_1_button.config(state='disabled')  # 禁用-1按钮
            self.increase_1_button.config(state='disabled')  # 禁用+1按钮
            self.increase_100_button.config(state='disabled')  # 禁用+100按钮
            self.set_frequency_button.config(state='disabled')  # 禁用设置按钮
            self.time_sync_button.config(state='disabled')  # 禁用时间同步按钮
            self.sync_button.config(state='disabled')  # 禁用参数同步按钮
            self.firmware_button.config(state='disabled')  # 禁用固件信息按钮

    def show_error_message(self, message):
        """显示错误信息"""
        # 这里你可以选择用弹窗、日志或者其他方式提示用户
        self.log_info(f"错误: {message}")

    def start_status_updates(self):
        """开始定时请求一系列的状态信息"""
        self.request_status_info()  # 立刻请求一次状态信息
        self._schedule_next_request()  # 设置后续的定时请求

    def stop_status_updates(self):
        """停止状态更新"""
        if self.update_status_id:
            self.root.after_cancel(self.update_status_id)  # 取消当前定时器
            self.update_status_id = None

    def _schedule_next_request(self):
        """设置下一次请求的定时器"""
        self.update_status_id = self.root.after(333, self.request_status_info)  # 每330ms请求一次

    def request_status_info(self):
        """请求频率、电源电压、漏极电流、发射功率、驻波比和发射状态"""
        commands = [
            '?F\r',   # 频率
            '?IB\r',  # 电源电压
            '?ID\r',  # 漏极电流
            '?IP\r',  # 发射功率
            '?IS\r',  # 驻波比
            '?B\r'    # 发射状态
        ]
        if self.serial_port and self.serial_port.is_open:
            for command in commands:
                try:
                    self.serial_port.write(command.encode('utf-8'))
                    response = self.serial_port.readline().decode('utf-8').strip()
                    self.update_status_display(response)
                except Exception as e:
                    self.log_info(f"错误: {str(e)}")  # 错误日志
        self._schedule_next_request() # 设置下次请求

    def update_status_display(self, response):
        """更新状态栏显示"""
        if response.startswith('=F'):
            frequency = int(response[2:])  # 提取频率
            self.frequency = frequency
            self.current_frequency_value.set(f"{self.frequency}")
        elif response.startswith('=IB'):
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
                self.transmit_status_label.config(text="状态: 接收", foreground="green")
                
    def send_firmware_info(self):
        """发送固件信息请求"""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(b"?II\r")
            response = self.serial_port.readline().decode('utf-8').strip()
            self.log_info(f"固件信息: {response[3:]}")
            
    # ----------------------基础设置区域设置----------------------
    
    def change_mode(self, event=None):
        """切换电台模式"""
        value = self.mode_combobox.current()
        if self.serial_port and self.serial_port.is_open:
            command = f"=G{value}\r".encode('utf-8')
            self.serial_port.write(command)
            self.log_info(f"模式已切换: {self.mode_combobox.get()}")
            
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
    
    # ----------------------信息区与调试设置----------------------
    
    def log_info(self, message):
        """记录信息到文本框"""
        self.info_text.config(state='normal')
        self.info_text.insert(tk.END, message + "\n")
        self.info_text.config(state='disabled')
        self.info_text.yview(tk.END)
        
    def send_command(self):
        """输入发送与直接接收串口命令"""
        text = self.command_entry.get()
        
        if self.serial_port and self.serial_port.is_open:
            try:
                command = f"{text}\r".encode('utf-8')
                self.serial_port.write(command)
                self.log_info(f" => 已发送： {text}\r")
            except:
                self.log_info(f"发送命令时发生错误")
            response = self.serial_port.readline().decode('utf-8').strip()
            self.log_info(response)
        else:
            self.log_info("请先连接串口")
            
    # ----------------------信息输入区设置----------------------
    
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
    
    # ----------------------参数、时间同步----------------------
    
    def send_time_sync(self):
        """读取当前系统时间并同步"""
        current_time = time.localtime()
        total_seconds = current_time.tm_min * 60 + current_time.tm_sec
        if 1 <= total_seconds <= 3599:
            command = f"=N{total_seconds:04d}\r".encode('utf-8')
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.write(command)
                self.log_info(f"时间同步已发送: {total_seconds // 60:02d}:{total_seconds % 60:02d}")
        else:
            self.log_info("时间超出范围")
            
    def request_current_settings(self):
        """询问当前设置并更新UI"""
        queries = ['?G\r', '?O\r', '?P\r']
        self.log_info(f"尝试发送基本参数同步请求")
        for query in queries:
            if self.serial_port and self.serial_port.is_open:
                try:
                    self.serial_port.write(query.encode('utf-8'))
                    response = self.serial_port.readline().decode('utf-8').strip()
                    self.update_settings(response)
                except Exception as e:
                    self.log_info(f"错误: {str(e)}")

    def update_settings(self, response, event=None):
        """更新UI中的设置值"""
        if response.startswith('=G'):
            mode_index = int(response[2])
            self.mode_combobox.current(mode_index)

        elif response.startswith('=O'):
            operation_mode_index = int(response[2])
            self.operation_mode_combobox.current(operation_mode_index)

        elif response.startswith('=P'):
            power_index = int(response[2])
            self.power_combobox.current(power_index)
            
    #============================================================
    #                        进阶事件函数
    #============================================================
    
    # ----------------------接受设置----------------------
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
    
    # ----------------------GPS设置----------------------
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
                self.gps_value_result.config(text=response[2:])
                self.log_info(f"GPS定位器值: {response[2:]}")
            except Exception as e:
                self.log_info(f"错误: {str(e)}")

    # ----------------------设备关键设置----------------------            
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

    def send_spare_io_setting(self, event=None):
        """发送SPARE I/O设置指令"""
        index = self.spare_io_combobox.current()
        command = f"=X{index}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"SPARE I/O设置: {self.spare_io_combobox.get()}")

    def send_callsign(self):
        """设置呼号"""
        text = self.callsign_entry.get()
        command = f"=Z{text}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"发送呼号: {text}")      

    def send_grid(self):
        """设置网格"""
        text = self.grid_entry.get()
        command = f"=L{text}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"发送网格坐标: {text}")

    def send_cw_identity(self, event=None):
        """设置结束CW识别码发送"""
        value = self.cw_identity_combobox.current()
        command = f"=Y{value}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"发送CW识别: {self.cw_identity_combobox.get()}")            
    
    # ----------------------需要输入框的设置----------------------
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

    def send_script_text(self):
        """设置自动脚本内容"""
        text = self.script_text_entry.get()
        command = f"=U{text}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"发送自动脚本文本: {text}")
            
    # ----------------------CW/QRSS/DFCW设置----------------------      
    def set_cw_mode(self, event=None):
        """设置CW电键模式"""
        value = self.cw_mode_combobox.current()
        command = f"=K{value}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"CW电键模式已设置: {self.cw_mode_combobox.get()}")

    def send_cw_speed(self, event=None):
        """设置CW WPM速度"""
        value = int(self.cw_speed_combobox.get()) * 10  # 从下拉菜单获取值并乘以10
        command = f"=S{value}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"发送CW速度: {value // 10}")

    def send_interval_setting(self, event=None):
        """发送CW\QRSS\DFCW发送间隔设置指令"""
        interval_index = self.interval_combobox.current()
        command = f"=Q{interval_index}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"CW/QRSS/DFCW发射帧已设置: {self.interval_combobox.get()}")

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
            
    # ----------------------JASON/OPERA/WSQ设置----------------------            
    def send_jason_interval_setting(self, event=None):
        """发送JASON消息发射间隔设置指令"""
        interval_index = self.jason_interval_combobox.current()
        command = f"=JF{interval_index}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(command)
            self.log_info(f"JASON发射帧已设置: {self.jason_interval_combobox.get()}")

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
             self.log_info(f"OPERA发射帧已设置: {self.opera_frame_combobox.get()}")

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
        command = f"=QF{wsq_index}\r".encode('utf-8')
        if self.serial_port and self.serial_port.is_open:
             self.serial_port.write(command)
             self.log_info(f"WSQ发射帧已设置: {self.wsq_frame_combobox.get()}")

    # ----------------------JASON/OPERA/WSQ设置----------------------
    def send_wspr_power_setting(self, event=None):
        """发送WSPR功率设置指令"""
        power_value = self.wspr_power_combobox.get()
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
            
    # ----------------------Script/REMOTE设置----------------------
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
            
    # ----------------------进阶参数同步----------------------        
    def sync_settings(self):
        """同步设备设置并更新UI"""
        queries = ['?A\r', '?C\r', '?V\r', '?W\r', '?T\r', '?X\r', '?Z\r', '?L\r', 
                   '?Y\r', '?E\r', '?H\r', '?U\r', '?K\r', '?S\r', '?Q\r', '?D\r', 
                   '?R\r', '?JF\r', '?JS\r', '?OF\r', '?OS\r', '?Q\r', '?QF\r', '?WP\r', 
                   '?WS\r', '?WF\r', '?WT\r', '?WG\r', '?TF\r', '?TS\r', '?SF\r', '?RS\r']
        self.log_info(f"尝试发送进阶参数同步请求")
        for query in queries:
            if self.serial_port and self.serial_port.is_open:
                try:
                    # 发送查询命令
                    self.serial_port.write(query.encode('utf-8'))
                    # 读取响应并去除换行符
                    response = self.serial_port.readline().decode('utf-8').strip()
                    # 更新UI设置
                    self.update_advanced_settings(response)
                except Exception as e:
                    self.log_info(f"错误: {str(e)}")

    def update_advanced_settings(self, response):
        """解析响应并更新UI"""
        if response.startswith('=JF'):
            index = int(response[3])
            self.jason_interval_combobox.current(index)
        elif response.startswith('=JS'):
            index = int(response[3]) - 2
            self.jason_speed_combobox.current(index)
        elif response.startswith('=OF'):
            index = int(response[3])
            self.opera_frame_combobox.current(index)
        elif response.startswith('=OS'):
            index = int(response[3])
            self.opera_speed_combobox.current(index)
        elif response.startswith('=QF'):  #回复格式应为=QF0x
            index = int(response[3:])
            self.wsq_frame_combobox.current(index)
        elif response.startswith('=WP'):
            index = int(response[3:])
            self.wspr_power_combobox.current(index)
        elif response.startswith('=WS'):
            index = int(response[3])
            self.wspr_speed_combobox.current(index)
        elif response.startswith('=WF'):
            index = int(response[3])
            self.wspr_frame_combobox.current(index)
        elif response.startswith('=WT'):
            index = int(response[3])
            self.fst4w_speed_combobox.current(index)
        elif response.startswith('=WG'):
            index = int(response[3])
            self.fst4w_frame_combobox.current(index)
        elif response.startswith('=TF'):
            index = int(response[3])
            self.jt9_frame_combobox.current(index)
        elif response.startswith('=TS'):
            index = int(response[3])
            self.jt9_speed_combobox.current(index)
        elif response.startswith('=SF'):
            index = int(response[3])
            self.script_frame_combobox.current(index)
        elif response.startswith('=RS'):
            index = int(response[3])
            self.remote_combobox.current(index)
        elif response.startswith('=A'):
            index = int(response[2])
            self.preamplifier_combobox.current(index)
        elif response.startswith('=C'):
            index = int(response[2])
            self.upconverter_combobox.current(index)
        elif response.startswith('=V'):
            index = int(response[2])
            self.gps_locator_combobox.current(index)
        elif response.startswith('=W'):
            self.gps_value_result.config(text=response[2:])
        elif response.startswith('=T'):
            index = int(response[2])
            self.tx_control_combobox.current(index)
        elif response.startswith('=X'):
            index = int(response[2])
            self.spare_io_combobox.current(index)
        elif response.startswith('=Z'):
            self.callsign_entry.delete(0, tk.END)
            self.callsign_entry.insert(0, response[2:])
        elif response.startswith('=L'):
            self.grid_entry.delete(0, tk.END)
            self.grid_entry.insert(0, response[2:])
        elif response.startswith('=Y'):
            index = int(response[2])
            self.cw_identity_combobox.current(index)
        elif response.startswith('=E'):
            self.cw_beacon_entry.delete(0, tk.END)
            self.cw_beacon_entry.insert(0, response[2:])
        elif response.startswith('=H'):
            self.beacon_text_entry.delete(0, tk.END)
            self.beacon_text_entry.insert(0, response[2:])
        elif response.startswith('=U'):
            self.script_text_entry.delete(0, tk.END)
            self.script_text_entry.insert(0, response[2:])
        elif response.startswith('=K'):
            index = int(response[2])
            self.cw_mode_combobox.current(index)
        elif response.startswith('=S'):
            value = int(response[2:]) // 10
            self.cw_speed_combobox.set(str(value))
        elif response.startswith('=Q'): #回复格式应为=Q0x
            index = int(response[2:])
            self.interval_combobox.current(index)
        elif response.startswith('=D'):
            value = int(response[2:])
            self.dot_time_combobox.set(str(value))
        elif response.startswith('=R'):
            value = int(response[2:]) / 10
            self.dfcw_shift_combobox.set(str(value))





    
          
if __name__ == "__main__":
    root = tk.Tk()
    app = SerialControlApp(root)
    root.mainloop()
