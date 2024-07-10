import cv2
import numpy as np
import pyautogui
import time
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
import threading
import os
import webbrowser
import sounddevice as sd
import soundfile as sf
from scipy.io.wavfile import write
from moviepy.editor import VideoFileClip, AudioFileClip
from pydub import AudioSegment
import sys

# 設置錄製參數
fps = 25.0


# 取得 exe 檔案的目錄路徑
pwd = os.path.dirname(os.path.realpath(sys.argv[0]));

output_path = pwd + "\\output"

if os.path.isdir(output_path) == False:
    # 建目錄
    os.mkdir(output_path)

video_file = output_path + "\\output.mp4"
audio_mic_file = output_path + "\\output_mic.wav"
audio_system_file = output_path + "\\output_system.wav"
output_file = output_path + "\\final_output.mp4"

# 錄製狀態
recording = False
out = None
record_area = None
x1, y1, x2, y2 = 0, 0, 0, 0

def select_area():
    global x1, y1, x2, y2, record_area
    record_area = tk.Toplevel()
    record_area.attributes("-fullscreen", True)
    record_area.attributes("-alpha", 0.3)
    record_area.configure(background='black')

    instruction = tk.Label(record_area, text="用滑鼠選擇錄影範圍，按 Enter 鍵確認", bg="white")
    instruction.pack()

    canvas = tk.Canvas(record_area, cursor="cross")
    canvas.pack(fill="both", expand=True)

    rect = None

    def on_button_press(event):
        global rect, x1, y1
        x1, y1 = event.x, event.y
        rect = canvas.create_rectangle(event.x, event.y, event.x, event.y, outline='red')

    def on_move_press(event):
        global rect, x1,y1, x2, y2        
        x2, y2 = event.x, event.y
        canvas.coords(rect, x1, y1, x2, y2)

    def on_button_release(event):
        record_area.grab_release()  # 釋放滑鼠事件
        record_area.destroy()

    canvas.bind("<ButtonPress-1>", on_button_press)
    canvas.bind("<B1-Motion>", on_move_press)
    canvas.bind("<ButtonRelease-1>", on_button_release)

    record_area.grab_set_global()  # 捕獲滑鼠事件

def start_recording():
    global output_path
    global video_file
    global audio_mic_file
    global audio_system_file
    global output_file
    t = str(int(time.time()))
    video_file = output_path + "\\" + t + "_tmp.mp4"
    audio_mic_file = output_path + "\\" + t + "_mic_tmp.wav"
    audio_system_file = output_path + "\\" + t + "_system_tmp.wav"
    output_file = output_path + "\\" + t + ".mp4"
    
    global x1, x2, y1, y2
    print("x1, y1: %s, %s" % (x1,y1))
    print("x2, y2: %s, %s" % (x2,y2))
    global recording, out, video_thread, audio_mic_thread, audio_system_thread
    if recording:
        messagebox.showwarning("警告", "錄影已經在進行中！")
        return
    if x1 == x2 or y1 == y2:
        messagebox.showwarning("警告", "請先選擇錄影範圍！")
        return
    recording = True
    out = cv2.VideoWriter(video_file, cv2.VideoWriter_fourcc(*"mp4v"), fps, (x2 - x1, y2 - y1))
    video_thread = threading.Thread(target=record_video)
    audio_mic_thread = threading.Thread(target=record_mic_audio)
    audio_system_thread = threading.Thread(target=record_system_audio)
    video_thread.start()
    audio_mic_thread.start()
    audio_system_thread.start()
    start_button.config(state=tk.DISABLED)
    stop_button.config(state=tk.NORMAL)

def record_video():
    global recording, out
    while recording:
        img = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))
        frame = np.array(img)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        out.write(frame)
        cv2.imshow("Recording", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    out.release()
    cv2.destroyAllWindows()

def record_mic_audio():
    global audio_mic_file   
    global recording
    samplerate = 44100
    channels = 2    
    # 開啟音訊檔案準備寫入
    with sf.SoundFile(audio_mic_file, mode='x', samplerate=samplerate, channels=channels) as file:
        with sd.InputStream(samplerate=samplerate, channels=channels, device=1) as stream:
            print('錄製麥克風聲音開始...')
            while recording:
                data, overflowed = stream.read(1024)
                file.write(data)
            print('錄製麥克風聲音結束.')
print(sd.query_devices())                
def record_system_audio():
    global audio_system_file
    global recording
    samplerate = 44100
    channels = 2

    # 開啟音訊檔案準備寫入
    with sf.SoundFile(audio_system_file, mode='x', samplerate=samplerate, channels=channels) as file_system:
        # 使用 OutputStream 寫入系統聲音
        with sd.InputStream(samplerate=samplerate, channels=channels, device=2) as sys_stream:
            print('錄製系統聲音開始...')
            while recording:
                data, overflowed = sys_stream.read(1024)
                file_system.write(data)
            print('錄製系統聲音結束.')

def stop_recording():
    global recording, out, video_thread, audio_mic_thread, audio_system_thread
    if not recording:
        messagebox.showwarning("警告", "錄影未開始！")
        return
    recording = False
    video_thread.join()
    audio_mic_thread.join()
    audio_system_thread.join()
    start_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)
    messagebox.showinfo("提示", "錄影已停止")
    time.sleep(3) # Wait 3sec
    merge_audio_video()

def merge_audio_video():
    global audio_mic_file
    global audio_system_file
    global output_path
    video_clip = VideoFileClip(video_file)

    # 讀取系統聲音音訊檔案
    audio_system = AudioSegment.from_wav(audio_system_file)

    # 讀取麥克風音訊檔案
    audio_mic = AudioSegment.from_wav(audio_mic_file)

    # 合併音訊
    combined_audio = audio_system.overlay(audio_mic)

    # 將合併後的音訊寫入新檔案
    tmp_file = output_path + "\\" + str(int(time.time()))+"_merge.wav"
    combined_audio.export(tmp_file, format='wav')

    final_audio_clip = AudioFileClip(tmp_file)    

    # 將合併後的音訊剪輯添加到視訊剪輯中
    final_clip = video_clip.set_audio(final_audio_clip)
    
    final_clip.write_videofile(output_file, codec='libx264', audio_codec='aac')
    if os.path.isfile(video_file):
        try:
            os.remove(video_file)
        except:
            pass
    if os.path.isfile(audio_mic_file):
        try:
            os.remove(audio_mic_file)
        except:
            pass
    if os.path.isfile(audio_system_file):
        try:
            os.remove(audio_system_file)
        except:
            pass
    if os.path.isfile(tmp_file):
        try:
            os.remove(tmp_file)
        except:
            pass

def open_folder():
    folder_path = os.path.dirname(os.path.abspath(output_file))
    webbrowser.open(folder_path)

def on_closing():
    if recording:
        if messagebox.askokcancel("離開", "錄影正在進行，確定要離開嗎？"):
            stop_recording()
            root.destroy()
    else:
        root.destroy()

# 函數：鼠標按下時的位置
def win_start_move(event):
        root.x = event.x
        root.y = event.y

def win_stop_move(event):
    root.x = None
    root.y = None

def win_do_move(event):
    deltax = event.x - root.x
    deltay = event.y - root.y
    x = root.winfo_x() + deltax
    y = root.winfo_y() + deltay
    root.geometry(f"+{x}+{y}")
root = tk.Tk()

root.title(u"桌面錄影")

select_area_button = tk.Button(root, text="選擇錄影範圍", command=select_area)
select_area_button.pack(pady=10)

start_button = tk.Button(root, text="開始錄影", command=start_recording)
start_button.pack(pady=10)

stop_button = tk.Button(root, text="停止錄影", command=stop_recording, state=tk.DISABLED)
stop_button.pack(pady=10)

open_folder_button = tk.Button(root, text="打開錄影資料夾", command=open_folder)
open_folder_button.pack(pady=10)

exit_button = tk.Button(root, text="離開程式", command=on_closing)
exit_button.pack(pady=10)

root.protocol("WM_DELETE_WINDOW", on_closing)

# 綁定標題欄的鼠標按下事件
root.bind("<ButtonPress-1>", win_start_move)
root.bind("<ButtonRelease-1>", win_stop_move)
root.bind("<B1-Motion>", win_do_move)

root.mainloop()