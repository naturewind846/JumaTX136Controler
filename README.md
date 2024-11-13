# JumaTX136Controler
仓库包含了原始jumatx136的相关资料和我自己写的juma tx136 v1.15的python桌面端控制程序

JumaTX136_origindoc文件夹包含官方原始的制作资料、电路图、源代码、BOM单、dspic写入程序和控制程序

TX136_1,15_doc包含了最新的第三方固件、文档和AFP工具的Arduino源代码

serialafp test.py 是用于测试串口发送AFP指令的小工具

Juma TX136 AFP串口fsk.py 使用FFT、零填充和抛物线插值的方法，用于读取麦克风，配合VB-Audio Virtual Cable，可以用于发射FSK音频，更新周期20ms，频率精度0.02Hz。实测可以完美发送FST4、FST4W、WSPR等FSK模式

jumatx136 v1.1.py 目前已经实现全部串口控制功能，由于py上tk比较卡，正在考虑重写。
