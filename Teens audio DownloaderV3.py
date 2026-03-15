import tkinter as tk
from tkinter import messagebox
import requests
from bs4 import BeautifulSoup
import os
from PIL import Image, ImageTk
import re
import threading
import queue
def findvol(lst):
    """
    遍历列表，返回第一个符合模式 '[初/高][一/二/三] 第[数字]期' 的字符串。
    
    参数:
        lst (list): 待检查的列表，元素应为字符串。
    
    返回:
        str or None: 第一个匹配的字符串，若无匹配则返回 None。
    """
    pattern = re.compile(r'^[初高][一二三] 第\d+期$')
    for item in lst:
        item=item.get_text()
        if isinstance(item, str) and pattern.match(item):
            return item
    return None
def findhref(lst):
    """
    遍历列表，返回第一个符合模式 '[初/高][一/二/三] 第[数字]期' 的字符串。
    
    参数:
        lst (list): 待检查的列表，元素应为字符串。
    
    返回:
        str or None: 第一个匹配的字符串，若无匹配则返回 None。
    """
    pattern = re.compile(r'^[初高][一二三] 第\d+期$')
    for item in lst:
        it=item
        item=item.get_text()
        if isinstance(item, str) and pattern.match(item):
            return it.get("href")
    return None
def getindexurl(grade):
    grade=int(grade)
    if (grade<=3):
        return f"https://m.i21st.cn/paper/index_21je{grade}_1.html"
    else:
        return f"https://m.i21st.cn/paper/index_21se{grade-3}_1.html"
def on_button_click():
    grade=gradevar.get()
    header={'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ''Chrome/112.0.0.0 Safari/537.36'}
    res=requests.get(url=getindexurl(grade),headers=header)
    if res.status_code==200:
        soup = BeautifulSoup(res.content, 'html.parser')
        href="https://m.i21st.cn"+findhref(soup.find_all("a"))
    else :
        label.config(text="连接服务器错误，状态码："+str(res.status_code))
        root.update_idletasks()
        return 
    #print(soup.find_all("a"))
    result = messagebox.askokcancel("确认下载", "即将下载："+findvol(soup.find_all("a")))
    
        
    if result:

        download(href,header,soup,res,findvol(soup.find_all("a")),root,label)
def getname(grade,input_text):
    map=["","初一","初二","初三","高一","高二","高三"]
    return f"{map[int(grade)]} "+"第"+str(input_text)+"期"
def on_input_button_click():
    grade=gradevar.get()
    input_text = input_entry.get()
    
    try:
        input_text=int (input_text)
    except:
        label.config(text="期数要为整数！！！")
        return
    header={'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ''Chrome/112.0.0.0 Safari/537.36'}
    res=requests.get(url=getindexurl(grade),headers=header)
    
    if res.status_code==200:
        soup = BeautifulSoup(res.content, 'html.parser')
        try:
            href="https://m.i21st.cn"+soup.find('a', class_='wrapno txt-18', string=lambda text: text and getname(grade,input_text)==text).get("href")
        except:
            label.config(text="未找到指定期数的报纸！！")
            root.update_idletasks()
            return
    else :
        label.config(text="连接服务器错误，状态码："+str(res.status_code))
        root.update_idletasks()
        return 
    result = messagebox.askokcancel("确认下载", "即将下载："+soup.find('a', class_='wrapno txt-18', string=lambda text: text and getname(grade,input_text)==text).get_text())
    
    if result:

        download(href,header,soup,res,soup.find('a', class_='wrapno txt-18', string=lambda text: text and getname(grade,input_text)==text).get_text(),root,label)
    



def download(href, header, soup, res, fpath, root, label):
    msg_queue = queue.Queue()

    def update_gui():
        """主线程定期调用的函数，从队列获取消息并更新 GUI"""
        try:
            while True:
                msg = msg_queue.get_nowait()
                if msg == "DONE":
                    label.config(text="下载完成！")
                    break
                elif msg.startswith("ERROR:"):
                    label.config(text=msg[6:])
                elif msg.startswith("AUDIO:"):
                    # 格式：AUDIO:音频链接|名称
                    parts = msg[6:].split('|', 1)
                    if len(parts) == 2:
                        label.config(text=f"音频链接:{parts[0]} 名称:{parts[1]}")
                root.update_idletasks()
        except queue.Empty:
            pass
        root.after(100, update_gui)

    def download_task():
        try:
            os.makedirs(fpath, exist_ok=True)
        except Exception as e:
            msg_queue.put(f"ERROR:创建目录失败 {e}")
            return

        # 原代码中 if (1231==1231) 永远成立，直接执行
        audiohtmlres = requests.get(url=href, headers=header)
        if audiohtmlres.status_code == 200:
            audiohtmlsoup = BeautifulSoup(audiohtmlres.content, "html.parser")
            audio_name = []
            audio_urls = []
            for audiohtmlurl in audiohtmlsoup.find_all("a", class_="wrapno txt-16"):
                print("html url:", audiohtmlurl.get("href"), "audio name:", audiohtmlurl.get_text())
                audio_urls.append(audiohtmlurl.get("href"))
                audio_name.append(audiohtmlurl.get_text())

            for i in range(len(audio_urls)):
                audiores = requests.get(url=audio_urls[i], headers=header)
                if audiores.status_code == 200:
                    audiosoup = BeautifulSoup(audiores.content, "html.parser")
                    audio_src = audiosoup.find("audio").get("src")
                    # 发送更新消息到主线程
                    msg_queue.put(f"AUDIO:{audio_src}|{audio_name[i]}")

                    # 下载音频文件（注意 headers 要包含 Referer）
                    audio = requests.get(
                        headers={
                            "Referer": "https://paper.i21st.cn/",
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0"
                        },
                        url=audio_src
                    )
                    file_path = os.path.join(fpath, f"{audio_name[i]}.mp3")
                    with open(file_path, "wb") as f:
                        f.write(audio.content)
                else:
                    msg_queue.put(f"ERROR:获取{audio_name[i]}音频发生错误")

            msg_queue.put("DONE")
        else:
            vol_name = findvol(soup.find_all("a"))  # 假设你有这个函数
            msg_queue.put(f"ERROR:获取{vol_name}的具体内容时发生错误")

    # 启动后台线程
    t = threading.Thread(target=download_task)
    t.daemon = True  # 主线程退出时自动结束
    t.start()

    # 启动 GUI 更新循环
    root.after(100, update_gui)


root = tk.Tk()
root.title("报纸音频下载器")
import sys
bundle_dir = getattr(sys, '_MEIPASS')
 

data_file_path = os.path.join(bundle_dir)
path=os.path.join(bundle_dir,'icon.ico')
root.iconbitmap(path)
root.geometry("700x400")
gradevar = tk.StringVar()

radio1 = tk.Radiobutton(root, text="初一", variable=gradevar, value="1")
radio2 = tk.Radiobutton(root, text="初二", variable=gradevar, value="2")
radio3 = tk.Radiobutton(root, text="初三", variable=gradevar, value="3")
radio4 = tk.Radiobutton(root, text="高一", variable=gradevar, value="4")
radio5 = tk.Radiobutton(root, text="高二", variable=gradevar, value="5")
radio6 = tk.Radiobutton(root, text="高三", variable=gradevar, value="6")


radio1.pack()
radio2.pack()
radio3.pack()
radio4.pack()
radio5.pack()
radio6.pack()

label = tk.Label(root, text="")
label.pack(pady=10)


button = tk.Button(root, text="点击下载最新Teens", command=on_button_click)
button.pack(pady=10)
input_entry = tk.Entry(root, width=4)
input_entry.pack(pady=10)


input_button = tk.Button(root, text="下载特定期数Teens", command=on_input_button_click)
input_button.pack(pady=10)

root.mainloop()
