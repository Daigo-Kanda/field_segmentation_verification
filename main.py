import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from PIL import Image, ImageTk, ImageOps
import PIL.ExifTags as ExifTags
import os
from functools import partial
import glob
import xml.etree.ElementTree as ET
import ast
import time
#from numda import jit


class Application(tk.Frame):
    def __init__(self, master=None):
        #パスの初期値設定（例外処理のため）
        self.folder_name = "none"
        self.original_folder_name = "none"
        self.mask_folder_name = "none"
        self.counter=0
        self.check_label_num = 0
        self.status_count = 0
        self.color=[[255,0,0],[255,165,0],[255,255,0],[173,255,47],[0,128,0],[102,205,170],[135,206,235],[0,0,255],[128,0,128]]
        #["赤","オレンジ","黄色","黄緑","緑","青緑","水色","青","紫"]
        super().__init__(master)

        # ウィンドウタイトル
        self.master.title("mask_label_check")

        self.master.geometry("800x600")

        # メニューの作成
        self.create_menu()
        # ツールバーの作成
        #self.create_tool_bar()
        #プログレスバーの作成
        self.create_progress_bar()
        # ステータスバーの作成
        self.create_status_bar()
        # サイドパネル
        self.create_side_panel()


        # 残りの領域にキャンバスを作成
        self.back_color = "#008B8B"  # 背景色
        self.canvas = tk.Canvas(self.master, background=self.back_color)
        self.canvas.pack(expand=True, fill=tk.BOTH)

    def create_menu(self):
        ''' メニューの作成'''
        menu_bar = tk.Menu(self)

        file_menu = tk.Menu(menu_bar, tearoff=tk.OFF)
        menu_bar.add_cascade(label="ファイル", menu=file_menu)

        file_menu.add_command(label="開く(check_mask)", command=self.menu_open_click, accelerator="Ctrl+0")
        file_menu.add_command(label="開く(check_label)", command=self.menu_open_click_label, accelerator="Ctrl+1")
        file_menu.add_separator()  # セパレータ
        file_menu.add_command(label="終了", command=self.master.destroy)
        # ショートカットの設定
        #menu_bar.bind_all("", self.menu_open_click)

        # 親のメニューに設定
        self.master.config(menu=menu_bar)

    def menu_open_click(self, event=None):
        self.check_label_num=0
        self.status_count = 1
        self.canvas.delete("rect")
        self.canvas.delete("img")
        #ラベルテキスト変更
        self.label1["text"]=""
        self.label2["text"] = "読み込み中"
        ''' フォルダを開く'''
        # フォルダを開くダイアログ
        self.folder_name = tk.filedialog.askdirectory(
            initialdir=os.getcwd()  # カレントディレクトリ
        )
        self.original_folder_name=self.folder_name
        self.mask_folder_name = os.path.join(self.folder_name, "mask")

        #csvの読み取り
        self.df=pd.read_csv(os.path.join(self.folder_name,"inf.csv"), index_col=0)
        self.total_number = (self.df["mask_inf"] == 1).sum()
        if "mask_result" not in self.df.columns.tolist():
            self.df["mask_result"]=np.nan

        for index, row in self.df.iterrows():
            if row["mask_inf"]==0:
                continue
            else:
                file_name=index
                self.counter=self.df.index.get_loc(index)
                break

        # 画像の読み取り
        self.original_images_data=self.read_images("original")
        self.mask_images_data = self.read_images("mask")

        #canvas上に画像を表示
        self.display_image("original",self.counter)
        self.display_image("mask",0)

        #self.display_image(os.path.join(self.original_folder_name,str(file_name)+".JPG"),"original")
        #self.display_image(os.path.join(self.mask_folder_name, str(file_name) + ".npy"), "mask")
        self.label1["text"] = str(file_name)
        self.label2["text"] = str(self.status_count) + "/" + str(self.total_number)

    def menu_open_click_label(self):
        self.check_label_num = 1
        self.status_count = 1
        self.canvas.delete("rect")
        self.canvas.delete("img")
        # ラベルテキスト変更
        self.label1["text"] = ""
        self.label2["text"] = "読み込み中"
        # フォルダを開くダイアログ
        self.folder_name = tk.filedialog.askdirectory(
            initialdir=os.getcwd()  # カレントディレクトリ
        )
        self.original_folder_name=self.folder_name
        self.mask_folder_name = os.path.join(self.folder_name, "mask")
        self.whole_area_path=os.path.join(os.path.dirname(os.path.dirname(self.original_folder_name)), "whole_area.JPG")
        self.size=os.path.basename(self.original_folder_name)
        self.df=pd.read_csv(os.path.join(self.folder_name,"inf.csv"), index_col=0)
        self.total_number=(self.df["mask_inf"]==1).sum()
        if "label_result" not in self.df.columns.tolist():
            self.df["label_result"]=np.nan
        for index, row in self.df.iterrows():
            if row["mask_inf"]==0:
                continue
            else:
                file_name=index
                self.counter=self.df.index.get_loc(index)
                break

        # 画像の読み取り
        self.read_gps_degree()  #gps&degreeの取得
        self.mask_images_data = self.read_images("mask")
        #canvas上に画像を表示
        self.display_image("whole_ara", 0)
        self.display_image("mask", 0)
        self.create_rectangle_in_whole_map(self.rotate(self.rectangle_coordinate(self.gps_list[self.counter],self.size),self.cal_theta()))

        self.label1["text"] = str(file_name)
        self.label2["text"] = str(self.status_count) + "/" + str(self.total_number)

    def create_tool_bar(self):
        ''' ツールバー'''

        frame_tool_bar = tk.Frame(self.master, borderwidth=2, relief=tk.SUNKEN)

        self.button_check_label = tk.Button(frame_tool_bar, text="check_label", width=10,
                                            command=lambda:self.button_click_check_label(), bg="#a9a9a9")

        self.button_check_label.pack(side=tk.LEFT)

        frame_tool_bar.pack(fill=tk.X)

    def create_progress_bar(self):
        frame_for_progress_bar=tk.Frame(self.master, borderwidth=2, relief=tk.SUNKEN)
        self.progress_bar=ttk.Progressbar(frame_for_progress_bar, length=500, value=0, maximum=100)
        self.label1_progress = tk.Label(frame_for_progress_bar, width=20 , text="")
        self.label2_progress = tk.Label(frame_for_progress_bar, width=10, text="")

        self.label1_progress.pack(side=tk.LEFT)
        self.progress_bar.pack(side=tk.LEFT)
        self.label2_progress.pack(side=tk.LEFT)

        frame_for_progress_bar.pack(fill=tk.X)

    def create_status_bar(self):
        '''ステータスバー'''
        frame_status_bar = tk.Frame(self.master, borderwidth=2, relief=tk.SUNKEN)

        self.label1 = tk.Label(frame_status_bar, text="ステータスラベル１")
        self.label2 = tk.Label(frame_status_bar, text="ステータスラベル２")

        self.label1.pack(side=tk.LEFT)
        self.label2.pack(side=tk.RIGHT)

        frame_status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_side_panel(self):
        '''サイドパネル'''
        side_panel = tk.Frame(self.master, borderwidth=2, relief=tk.SUNKEN)

        self.button1 = tk.Button(side_panel, text="〇", width=15, height=15, command=lambda:self.button_click1(), bg='#e60033')
        self.button2 = tk.Button(side_panel, text="×", width=15, height=15, command=lambda:self.button_click2(), bg='#0095d9')
        self.button3 = tk.Button(side_panel, text="1つ戻る", width=15, height=5, command=lambda:self.back_image(),
                                 bg='#a9a9a9')
        self.button1.pack()
        self.button2.pack()
        self.button3.pack()

        side_panel.pack(side=tk.RIGHT, fill=tk.Y)

    def button_click1(self):  #〇の場合
        #何も画像が表示されていないときにボタンを押しても何も起きない
        if self.folder_name == "none":
            return 0
        else:
            self.status_count+=1
            if self.check_label_num==1:  #label
                # csvファイルへの書き込み
                self.df["label_result"][self.counter] = 0
                # 次の画像データの読み込み
                self.counter += 1
                for self.counter in range(self.counter, len(self.df)):
                    if self.df["mask_inf"][self.counter] == 0:
                        continue
                    else:
                        file_name = self.df.index[self.counter]
                        break
                # csvファイル保存、終了
                if self.counter == len(self.df):
                    self.df.to_csv(os.path.join(self.folder_name, "inf.csv"))
                    # パスの初期値設定（例外処理のため）
                    self.folder_name = "none"
                    self.original_folder_name = "none"
                    self.mask_folder_name = "none"
                    self.counter = 0
                    self.msg_show("終了です")
                    return 0
                # canvas上の図形を削除
                self.canvas.delete("rect")

                # canvas上に画像を表示
                self.display_image("mask",self.status_count-1)
                #self.display_image(os.path.join(self.mask_folder_name, str(file_name) + ".npy"), "mask")

                # canvas上に図形を表示
                self.create_rectangle_in_whole_map(
                    self.rotate(self.rectangle_coordinate(self.gps_list[self.counter], self.size), self.cal_theta()))

            else:                        #mask
                #csvファイルへの書き込み
                self.df["mask_result"][self.counter]=0
                #次の画像データの読み込み
                self.counter += 1
                for self.counter in range(self.counter,len(self.df)):
                    if self.df["mask_inf"][self.counter] ==0:
                        continue
                    else:
                        file_name = self.df.index[self.counter]
                        break
                #csvファイル保存、終了
                if self.counter==len(self.df):
                    self.df.to_csv(os.path.join(self.folder_name,"inf.csv"))
                    # パスの初期値設定（例外処理のため）
                    self.folder_name = "none"
                    self.original_folder_name = "none"
                    self.mask_folder_name = "none"
                    self.counter = 0
                    self.msg_show("終了です")
                    return 0

                #canvas上に画像を表示
                self.display_image("original",self.counter)
                self.display_image("mask", self.status_count-1)
                #self.display_image(os.path.join(self.original_folder_name,str(file_name)+".JPG"),"original")
                #self.display_image(os.path.join(self.mask_folder_name, str(file_name) + ".npy"), "mask")
        self.label1["text"] = str(file_name)
        self.label2["text"] = str(self.status_count) + "/" + str(self.total_number)

    def button_click2(self):  #×の場合
        #何も画像が表示されていないときにボタンを押しても何も起きない
        if self.folder_name == "none":
            return 0
        else:
            self.status_count += 1
            if self.check_label_num==1:  #label
                # csvファイルへの書き込み
                self.df["label_result"][self.counter] = 0
                # 次の画像データの読み込み
                self.counter += 1
                for self.counter in range(self.counter, len(self.df)):
                    if self.df["mask_inf"][self.counter] == 0:
                        continue
                    else:
                        file_name = self.df.index[self.counter]
                        break
                # csvファイル保存、終了
                if self.counter == len(self.df):
                    self.df.to_csv(os.path.join(self.folder_name, "inf.csv"))
                    # パスの初期値設定（例外処理のため）
                    self.folder_name = "none"
                    self.original_folder_name = "none"
                    self.mask_folder_name = "none"
                    self.counter = 0
                    self.msg_show("終了です")
                    return 0
                # canvas上の図形を削除
                self.canvas.delete("rect")

                # canvas上に画像を表示
                self.display_image("mask", self.status_count-1)

                # canvas上に図形を表示
                self.create_rectangle_in_whole_map(
                    self.rotate(self.rectangle_coordinate(self.gps_list[self.counter], self.size), self.cal_theta()))

            else:                                      #mask
                #csvファイルへの書き込み
                self.df["mask_result"][self.counter]=1
                #次の画像データの読み込み
                self.counter += 1
                for self.counter in range(self.counter,len(self.df)):
                    if self.df["mask_inf"][self.counter] ==0:
                        continue
                    else:
                        file_name = self.df.index[self.counter]
                        break
                #csvファイル保存、終了
                if self.counter==len(self.df):
                    self.df.to_csv(os.path.join(self.folder_name, "inf.csv"))
                    # パスの初期値設定（例外処理のため）
                    self.folder_name = "none"
                    self.original_folder_name = "none"
                    self.mask_folder_name = "none"
                    self.counter = 0
                    self.msg_show("終了です")
                    return 0

                # canvas上に画像を表示
                self.display_image("original", self.counter)
                self.display_image("mask", self.status_count-1)

        self.label1["text"] = str(file_name)
        self.label2["text"] = str(self.status_count) + "/" + str(self.total_number)

    def back_image(self):  #１つ戻る
        if self.counter == 0:
            return 0
        orignal_status_counter = self.status_count
        self.status_count -= 1
        orignal_counter=self.counter
        #1つ前のパスを取得
        for self.counter in reversed(range(0,orignal_counter)):
            if self.df["mask_inf"][self.counter] == 0:
                if self.counter-1==0:  #戻る画像がない場合
                    self.counter=orignal_counter
                    self.status_count=orignal_status_counter
                    return 0
                continue
            else:
                file_name = self.df.index[self.counter]
                break
        if self.check_label_num==1:
            # canvas上の図形を削除
            self.canvas.delete("rect")

            # canvas上に画像を表示
            self.display_image("mask", self.status_count-1)

            # canvas上に図形を表示
            self.create_rectangle_in_whole_map(
                self.rotate(self.rectangle_coordinate(self.gps_list[self.counter], self.size), self.cal_theta()))
        else:
            # canvas上に画像を表示
            self.display_image("original", self.counter)
            self.display_image("mask", self.status_count-1)

        self.label1["text"] = str(file_name)
        self.label2["text"] = str(self.status_count) + "/" + str(self.total_number)

    def display_image(self, state, counter):  #1枚ずつ読み取る場合 display_image(self, filename, state)

        # キャンバスのサイズを取得
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if state == "original":
            image_pil = Image.fromarray(self.original_images_data[counter])  # RGBからPILフォーマットへ変換
            self.photo_image_original = ImageTk.PhotoImage(image_pil)  # ImageTkフォーマットへ変換
            self.canvas.create_image(
                self.canvas.winfo_width() / 2,  # 画像表示位置(Canvasの中心)
                self.canvas.winfo_height() / 4,
                image=self.photo_image_original,  # 表示画像データ
                tag="img"
            )
        elif state == "mask":
            image_gray=self.mask_images_data[counter]
            if self.check_label_num==1:
                pil_image = Image.fromarray(self.mask_images_data[counter])
                self.photo_image_mask_coloring = ImageTk.PhotoImage(image=pil_image)
                self.canvas.create_image(
                    canvas_width / 2,  # 画像表示位置(Canvasの中心)
                    canvas_height / 4,
                    image=self.photo_image_mask_coloring,  # 表示画像データ
                    tag="img"
                )
                self.coloring_area_in_whole_map(self.label_data[counter])
            else:
                #image_bin = (image_gray >= 1) * 255  # ２値化
                pil_image = Image.fromarray(self.mask_images_data[counter])  # RGBからPILフォーマットへ変換
                self.photo_image_mask = ImageTk.PhotoImage(image=pil_image)
                self.canvas.create_image(
                    canvas_width / 2,  # 画像表示位置(Canvasの中心)
                    canvas_height * 3 / 4,
                    image=self.photo_image_mask,  # 表示画像データ
                    tag="img"
                )
        else:
            pil_image = Image.open(self.whole_area_path)
            image_resize = ImageOps.pad(pil_image, (self.canvas.winfo_width(), int(self.canvas.winfo_height() / 2)),
                                        color=self.back_color)
            self.photo_image_whole_area = ImageTk.PhotoImage(image=image_resize)
            self.canvas.create_image(
                canvas_width / 2,  # 画像表示位置(Canvasの中心)
                canvas_height * 3 / 4,
                image=self.photo_image_whole_area,  # 表示画像データ
                tag="img"
            )

        """ 1枚ずつ画像を読み取る場合
        '''画像をCanvasに表示する'''
        if not filename:
            return 0
        if filename.split(".")[-1]=="JPG":
            # PIL.Imageで開く
            pil_image = Image.open(filename)
        else:
            image_gray = np.load(filename, allow_pickle=True)
            if self.check_label_num==1:
                label_list=self.inv_label(image_gray)
                image_color=self.mask_color_change(label_list,image_gray)
                pil_image = Image.fromarray(image_color)
            else:
                image_bin = (image_gray >= 1) * 255  #２値化
                pil_image = Image.fromarray(image_bin)  # RGBからPILフォーマットへ変換

        # 画像のアスペクト比（縦横比）を崩さずに指定したサイズ（キャンバスのサイズ）全体に画像をリサイズする
        pil_image = ImageOps.pad(pil_image, (canvas_width, int(canvas_height/2)), color=self.back_color)

        # PIL.ImageからPhotoImageへ変換する
        #self.photo_image = ImageTk.PhotoImage(image=pil_image)

        # 画像の描画
        if state == "original":
            # PIL.ImageからPhotoImageへ変換する
            self.photo_image_original = ImageTk.PhotoImage(image=pil_image)
            self.canvas.create_image(
                canvas_width / 2,  # 画像表示位置(Canvasの中心)
                canvas_height / 4,
                image=self.photo_image_original  # 表示画像データ
            )
        elif state == "mask":
            # PIL.ImageからPhotoImageへ変換する
            self.photo_image_mask = ImageTk.PhotoImage(image=pil_image)
            if self.check_label_num==1:

                self.canvas.create_image(
                    canvas_width / 2,  # 画像表示位置(Canvasの中心)
                    canvas_height / 4,
                    image=self.photo_image_mask  # 表示画像データ
                )
                self.coloring_area_in_whole_map(label_list)

            else:
                self.canvas.create_image(
                    canvas_width / 2,  # 画像表示位置(Canvasの中心)
                    canvas_height * 3 / 4,
                    image=self.photo_image_mask  # 表示画像データ
                )
        else:
            # PIL.ImageからPhotoImageへ変換する
            self.photo_image_whole_area = ImageTk.PhotoImage(image=pil_image)
            self.canvas.create_image(
                canvas_width / 2,  # 画像表示位置(Canvasの中心)
                canvas_height * 3 / 4,
                image=self.photo_image_whole_area  # 表示画像データ
            )
        """

    def msg_show(self,message):
        messagebox.showinfo("メッセージ", message)

    def input_status_msg(self,label,msg):
        label["text"]=msg

    def button_click_check_label(self):
        if self.button_check_label["bg"]=="#e60033":
            self.button_check_label.configure(bg="#a9a9a9")  #ボタンを元の色に戻す
            self.button_check_label.configure(relief="raised")
            self.check_label_num = 0
        else:
            self.button_check_label.configure(bg="#e60033")  #ボタンを赤
            self.button_check_label.configure(relief="sunken")
            self.check_label_num=1

    def mask_color_change(self,label_list,mask_img):  #inv_labelに統合
        r=g=b=(mask_img == 1) * 0
        color_img = np.zeros((mask_img.shape[0], mask_img.shape[1], 3))
        mask_img = np.stack([mask_img, mask_img, mask_img], 2)
        for k, label in enumerate(label_list):
            one_color_img = np.zeros((mask_img.shape[0], mask_img.shape[1], 3))
            one_color_img += [self.color[k][0],self.color[k][1],self.color[k][2]]
            color_img+=one_color_img*(mask_img==label)
        return color_img.astype(np.uint8)

    def inv_label(self,mask_img):
        label=[]
        plus_image=np.zeros((int(self.canvas.winfo_height() / 2), int(self.canvas.winfo_height() * 3 / 4),3))
        label_order=0
        for i in range(1,91):
            a=(mask_img==i)

            if a.any():
                label.append(i)
                pil_image = Image.fromarray(a)
                image_resize = pil_image.resize(
                    (int(self.canvas.winfo_height() * 3 / 4), int(self.canvas.winfo_height() / 2)))
                numpy_image = np.array(image_resize)
                color_img = [self.color[label_order][0], self.color[label_order][1],
                             self.color[label_order][2]] * np.stack([numpy_image, numpy_image, numpy_image], 2)
                plus_image += color_img
                label_order += 1
                """
                color_img = [self.color[label_order][0], self.color[label_order][1], self.color[label_order][2]] * np.stack([a, a, a], 2)
                pil_image = Image.fromarray(color_img.astype(np.uint8))
                image_resize = pil_image.resize(
                    (int(self.canvas.winfo_height() *3/4), int(self.canvas.winfo_height() / 2)))
                numpy_image = np.array(image_resize)
                plus_image+=numpy_image
                label_order+=1
                """
        return label,plus_image.astype(np.uint8)

    def coloring_area_in_whole_map(self,label_list):  #全域画像の指定区域の色付け
        # キャンバスのサイズを取得
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        for i, label in enumerate(label_list):
            label-=1
            row = label % 15 +1 #行番号
            column = label // 15 +1  #列番号
            rectangle = self.canvas.create_rectangle(canvas_width * (16.1 - 1.02*(row - 1)) / 17,
                                                     canvas_height * (11.0 - 0.92 * (column - 1)) / 12,
                                                     canvas_width * (16.9 - 1.02*(row - 1)) / 17,
                                                     canvas_height * (11.7 - 0.92 * (column - 1)) / 12,
                                                     fill=self.rgb2html(self.color[i]), tag="rect")
            """
            rectangle = self.canvas.create_rectangle(canvas_width * ( 16.1 -  (row - 1) ) / 17, canvas_height * ( 9.9 - 0.85*(column-1) ) / 12,
                                                     canvas_width * ( 16.9 -  (row - 1) ) / 17, canvas_height * ( 10.6 - 0.85*(column-1) ) / 12,
                                                     fill=self.rgb2html(self.color[i]), tag="rect")
            """

    def create_rectangle_in_whole_map(self,coordinates):  #座標をもとに画像領域と向きの→を作成
        x1 = coordinates[0]
        y1 = coordinates[1]
        x2 = coordinates[2]
        y2 = coordinates[3]
        x3 = coordinates[4]
        y3 = coordinates[5]
        x4 = coordinates[6]
        y4 = coordinates[7]
        arrow_x1 = coordinates[8]
        arrow_y1 = coordinates[9]
        arrow_x2 = coordinates[10]
        arrow_y2 = coordinates[11]
        self.canvas.create_line( x1, y1, x2, y2, x4, y4, x3, y3, x1, y1, fill = "white", width = 2,tag="rect")
        self.canvas.create_line(arrow_x1,arrow_y1,arrow_x2,arrow_y2,fill = "white",arrow="last",width = 2,tag="rect")

    def rotate(self,coordinates, theta):  #画像領域と→をドローンの角度情報をもとに回転
        x1 = coordinates[0]
        y1 = coordinates[1]
        x2 = coordinates[2]
        y2 = coordinates[3]
        x3 = coordinates[4]
        y3 = coordinates[5]
        x4 = coordinates[6]
        y4 = coordinates[7]
        x = coordinates[8]
        y = coordinates[9]
        arrow_x1=coordinates[10]
        arrow_y1=coordinates[11]
        arrow_x2=coordinates[12]
        arrow_y2=coordinates[13]
        theta = np.radians(theta)
        A = [[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]]
        [x1_new, y1_new] = np.dot(A, [x1-x, y1-y-self.canvas.winfo_height()/2])
        [x2_new, y2_new] = np.dot(A, [x2-x, y2-y-self.canvas.winfo_height()/2])
        [x3_new, y3_new] = np.dot(A, [x3-x, y3-y-self.canvas.winfo_height()/2])
        [x4_new, y4_new] = np.dot(A, [x4-x, y4-y-self.canvas.winfo_height()/2])
        [arrow_x1_new,arrow_y1_new]=np.dot(A, [arrow_x1-x,arrow_y1-y-self.canvas.winfo_height()/2])
        [arrow_x2_new, arrow_y2_new] = np.dot(A, [arrow_x2 - x, arrow_y2 - y - self.canvas.winfo_height() / 2])
        return x1_new+x, y1_new+y+self.canvas.winfo_height()/2, x2_new+x, y2_new+y+self.canvas.winfo_height()/2, \
               x3_new+x, y3_new+y+self.canvas.winfo_height()/2, x4_new+x, y4_new+y+self.canvas.winfo_height()/2, \
               arrow_x1_new+x, arrow_y1_new+y+self.canvas.winfo_height()/2,arrow_x2_new+x, arrow_y2_new+y+self.canvas.winfo_height()/2

    def length_per_pixel(self,cmos_size, focal_length, distance, image_size):
        horizontal = cmos_size[0] * distance / focal_length
        vertical = cmos_size[1] * distance / focal_length

        x_per_pixel = horizontal / image_size[0]
        y_per_pixel = vertical / image_size[1]

        return x_per_pixel, y_per_pixel

    def rectangle_size(self,height):  #canvas上における画像領域の大きさを計算、縦横のそれぞれの割合を出力
        whole_area_size=[70,28.8]
        size=[5472,3648]
        if height==10:
            x_per_pixel, y_per_pixel = self.length_per_pixel(cmos_size = [13.2, 8.8], focal_length = 8.8, distance = 10,
                                  image_size = size)
            percentage_of_image=[x_per_pixel*size[0]/whole_area_size[0],
                                 y_per_pixel*size[1]/whole_area_size[1]]
        elif height==12:
            x_per_pixel, y_per_pixel = self.length_per_pixel(cmos_size=[13.2, 8.8], focal_length=8.8, distance=12,
                                  image_size=size)
            percentage_of_image = [x_per_pixel * size[0] / whole_area_size[0],
                                   y_per_pixel * size[1] / whole_area_size[1]]
        else:
            x_per_pixel, y_per_pixel = self.length_per_pixel(cmos_size=[13.2,8.8], focal_length=8.8, distance=8,
                                                             image_size=size)
            percentage_of_image = [x_per_pixel * size[0] / whole_area_size[0],
                                   y_per_pixel * size[1] / whole_area_size[1]]
        return percentage_of_image

    def gcp_to_canvas(self,center):
        #gcp座標
        gcp0_lat = 36.11843383  # gcp8
        gcp0_lng = 140.0927344
        gcp1_lat=36.11864733  #gcp1
        gcp1_lng = 140.0934325
        gcp2_lat = 36.11855333  # gcp9
        gcp2_lng = 140.092677

        x_axis=np.array([gcp1_lat-gcp0_lat,gcp1_lng-gcp0_lng])
        y_axis =np.array([gcp2_lat - gcp0_lat, gcp2_lng - gcp0_lng])
        theta=np.arctan(x_axis[1]/x_axis[0])*-1
        A = [[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]]
        x_axis_rotate = np.dot(A, [x_axis[0], x_axis[1]])
        y_axis_rotate = np.dot(A, [y_axis[0], y_axis[1]])
        center_0=np.array([center[0]-gcp0_lat,center[1]-gcp0_lng])
        center_rotate=np.dot(A, center_0)
        center_rotate_syuusei=center_rotate
        #center_rotate_syuusei=center_rotate+np.array([y_axis_rotate[0]/y_axis_rotate[1]*center_rotate[1],0])
        x=0.83*self.canvas.winfo_width()*center_rotate_syuusei[0]/x_axis_rotate[0]+0.1*self.canvas.winfo_width()
        y=-(0.46*self.canvas.winfo_height()/2)*center_rotate_syuusei[1] / y_axis_rotate[1]+0.36*self.canvas.winfo_height()
        return [x,y]

    def rectangle_coordinate(self, center, size):
        #中心座標からcanvas上の位置に変換
        gps_ndarray = np.array(self.gps_list)
        #左上
        lng_min = min(gps_ndarray[:, 1])
        lat_lng_min = gps_ndarray[gps_ndarray[:, 1].argmin(), 0]
        #左下
        lat_min = min(gps_ndarray[:, 0])
        lng_lat_min = gps_ndarray[gps_ndarray[:, 0].argmin(), 1]
        #右上
        lat_max = max(gps_ndarray[:, 0])
        lng_lat_max = gps_ndarray[gps_ndarray[:, 0].argmax(), 1]
        #右下
        lng_max = max(gps_ndarray[:, 1])
        lat_lng_max = gps_ndarray[gps_ndarray[:, 1].argmax(), 0]

        #左上を原点とした座標系生成
        #右上
        migiue_x=lng_lat_max - lng_min
        migiue_y=-(lat_max - lat_lng_min)
        #左下
        hidarisita_x=lng_lat_min - lng_min
        hidarisita_y=-(lat_min - lat_lng_min)
        #画像中心座標
        center_x=center[1]-lng_min
        center_y=-(center[0]-lat_lng_min)

        #角度算出　マイナス方向の回転なので×‐１
        theta=np.arctan(migiue_y/migiue_x)*-1
        #回転(theta)
        A = [[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]]
        [rotate_migiue_x,rotate_migiue_y]=np.dot(A,[migiue_x,migiue_y])
        [rotate_hidarisita_x, rotate_hidarisita_y] = np.dot(A, [hidarisita_x, hidarisita_y])
        [rotate_center_x,rotate_center_y]=np.dot(A,[center_x,center_y])
        #手動でパラメータを調整
        x=1.15*self.canvas.winfo_width()*rotate_center_x/rotate_migiue_x-0.07*self.canvas.winfo_width()
        y=1.14*(self.canvas.winfo_height() /2)*rotate_center_y/rotate_hidarisita_y-0.15*(self.canvas.winfo_height() /2)
        #GCP座標を使用する場合
        #[x,y]=self.gcp_to_canvas(center)

        #撮影高度によってrectangleのサイズを変更
        if "10" in size:
            percentage = self.rectangle_size(10)
            rectangle_width = percentage[0] * self.canvas.winfo_width()
            rectangle_height = rectangle_width * 2 / 3
            x1 = x - rectangle_width / 2
            y1 = self.canvas.winfo_height() / 2 + y - rectangle_height / 2
            x2 = x - rectangle_width / 2
            y2 = self.canvas.winfo_height() / 2 + y + rectangle_height / 2
            x3 = x + rectangle_width / 2
            y3 = self.canvas.winfo_height() / 2 + y - rectangle_height / 2
            x4 = x + rectangle_width / 2
            y4 = self.canvas.winfo_height() / 2 + y + rectangle_height / 2
            arrow_x1 = x
            arrow_y1 = y1
            arrow_x2 = x
            arrow_y2 = y1 - 30
            return x1, y1, x2, y2, x3, y3, x4, y4, x, y, arrow_x1, arrow_y1, arrow_x2, arrow_y2
        elif "12" in size:
            percentage = self.rectangle_size(12)
            rectangle_width = percentage[0] * self.canvas.winfo_width()
            rectangle_height = rectangle_width * 2 / 3
            x1 = x - rectangle_width / 2
            y1 = self.canvas.winfo_height() / 2 + y - rectangle_height / 2
            x2 = x - rectangle_width / 2
            y2 = self.canvas.winfo_height() / 2 + y + rectangle_height / 2
            x3 = x + rectangle_width / 2
            y3 = self.canvas.winfo_height() / 2 + y - rectangle_height / 2
            x4 = x + rectangle_width / 2
            y4 = self.canvas.winfo_height() / 2 + y + rectangle_height / 2
            arrow_x1 = x
            arrow_y1 = y1
            arrow_x2 = x
            arrow_y2 = y1 - 30
            return x1, y1, x2, y2, x3, y3, x4, y4, x, y, arrow_x1, arrow_y1, arrow_x2, arrow_y2
        else:  #8m
            percentage=self.rectangle_size(8)
            rectangle_width=percentage[0]*self.canvas.winfo_width()  #画像領域のサイズの拡大するには*1.1する。他の高さのときも同様
            rectangle_height=rectangle_width*2/3  #画像領域のサイズの拡大するには*1.1する。他の高さのときも同様
            x1 = x - rectangle_width / 2
            y1 = self.canvas.winfo_height() / 2 + y - rectangle_height / 2
            x2 = x - rectangle_width / 2
            y2 = self.canvas.winfo_height() / 2 + y + rectangle_height / 2
            x3 = x + rectangle_width / 2
            y3 = self.canvas.winfo_height() / 2 + y - rectangle_height / 2
            x4 = x + rectangle_width / 2
            y4 = self.canvas.winfo_height() / 2 + y + rectangle_height / 2
            arrow_x1=x
            arrow_y1=y1
            arrow_x2=x
            arrow_y2=y1-30
            return x1,y1,x2,y2,x3,y3,x4,y4,x,y,arrow_x1,arrow_y1,arrow_x2,arrow_y2

    def cal_theta(self):
        degree=self.gimbal_degree_list[self.counter]
        return degree

    def rgb2html(self,rgb):
        html = "#"
        for i in range(3):
            html += hex(rgb[i])[2:].zfill(2)
        return html

    def read_gps_degree(self):
        self.gps_list = []
        self.gimbal_degree_list = []
        max = len(self.df.index)
        self.progress_bar.configure(value=0, maximum=max)
        if "gps_lat" in self.df.columns.tolist() and "gps_lng" in self.df.columns.tolist() and "degree" in self.df.columns.tolist():
            self.gps_list=np.stack([self.df["gps_lat"], self.df["gps_lng"]], 1).tolist()
            self.gimbal_degree_list=self.df["degree"].tolist()
            """   
        if os.path.isfile(os.path.join(self.original_folder_name, "gps_degree.csv")):
            df = pd.read_csv(os.path.join(self.original_folder_name, "gps_degree.csv"))
            self.gps_list=df["gps"].to_list()
            for i in range(len(self.gps_list)):
                self.gps_list[i]=eval(self.gps_list[i])
            self.gimbal_degree_list=df["degree"].to_list()
            """
        else:
            for i, image_path in enumerate(glob.glob(self.original_folder_name + "/*" + ".JPG")):
                pil_image = Image.open(image_path)
                # ドローンの角度を取得するための処理
                gimbal_yaw_degree = self.get_uav_azimuth(image_path)
                self.gimbal_degree_list.append(gimbal_yaw_degree)

                # 撮影画像中心のGPS座標を取得
                latlng = self.get_image_gps(pil_image)
                self.gps_list.append(latlng)
                self.progress_bar.configure(value=i)
                self.progress_bar.update()
                self.label1_progress["text"] = "gps&degree　読み込み中"
                self.label2_progress["text"] = str(i) + "/" + str(max)
            self.label1_progress["text"] = ""
            self.label2_progress["text"] = ""
            self.progress_bar.configure(value=0)
            dict = {"gps": self.gps_list, "degree": self.gimbal_degree_list}
            df = pd.DataFrame(dict)
            df.to_csv(os.path.join(self.original_folder_name, 'gps_degree.csv'))

    def read_images(self,state):
        datas = []
        if state == "original":
            self.gps_list = []
            self.gimbal_degree_list=[]
            pattern=".JPG"
            max=len(self.df.index)
            self.progress_bar.configure(value=0, maximum=max)
            for i, image_path in enumerate(glob.glob(self.original_folder_name+ "/*" +pattern)):

                if self.check_label_num==1 :  #gps,xmpの取得
                    pil_image = Image.open(image_path)
                    # ドローンの角度を取得するための処理
                    gimbal_yaw_degree = self.get_uav_azimuth(image_path)
                    self.gimbal_degree_list.append(gimbal_yaw_degree)

                    # 撮影画像中心のGPS座標を取得
                    latlng = self.get_image_gps(pil_image)
                    self.gps_list.append(latlng)
                    self.progress_bar.configure(value=i)
                    self.progress_bar.update()
                    self.label1_progress["text"] = "gps&degree　読み込み中"
                    self.label2_progress["text"] = str(i) + "/" + str(max)

                else:
                    pil_image = Image.open(image_path)
                    #image_resize = pil_image = ImageOps.pad(pil_image, (self.canvas.winfo_width(), int(self.canvas.winfo_height() / 2)))
                    image_resize = pil_image.resize((int(self.canvas.winfo_height() *3/4), int(self.canvas.winfo_height()/2)))
                    numpy_image = np.array(image_resize)
                    data_expanded = np.expand_dims(numpy_image, axis=0)
                    datas.append(data_expanded)
                    self.progress_bar.configure(value = i)
                    self.progress_bar.update()
                    self.label1_progress["text"]="original画像　読み込み中"
                    self.label2_progress["text"] = str(i)+"/"+str(max)
            if self.check_label_num==1:
                self.label1_progress["text"] = ""
                self.label2_progress["text"] = ""
                self.progress_bar.configure(value=0)
                return 0
            else:
                # (n_samples,height,width,channels)
                images_data = np.concatenate(datas, axis=0)
                self.label1_progress["text"] = ""
                self.label2_progress["text"] = ""
                self.progress_bar.configure(value=0)
                return images_data
        else:
            pattern=".npy"
            self.progress_bar.configure(value=0, maximum=self.total_number)
            images_data=[[]]
            self.label_data=[]
            for i, image_path in enumerate(glob.glob(self.mask_folder_name + "/*" + pattern)):
                image_gray = np.load(image_path, allow_pickle=True)
                pil_image = Image.fromarray(image_gray)
                image_resize = pil_image.resize(
                    (int(self.canvas.winfo_height() * 3 / 4), int(self.canvas.winfo_height() / 2)))
                numpy_image = np.array(image_resize)
                data_expanded = np.expand_dims(numpy_image, axis=0)
                datas.append(data_expanded)
                self.progress_bar.configure(value=i)
                self.progress_bar.update()
                self.label1_progress["text"] = "mask画像　読み込み中"
                self.label2_progress["text"] = str(i) + "/" + str(self.total_number)
            images_data = np.concatenate(datas, axis=0)
            self.label_data=self.df["label"].dropna().tolist()
            for i in range(len(self.label_data)):
                self.label_data[i] = ast.literal_eval(self.label_data[i])
                #self.label_data[i] = eval(self.label_data[i])
            self.label1_progress["text"] = ""
            self.label2_progress["text"] = ""
            self.progress_bar.configure(value=0)
            return images_data
            """
            for i, image_path in enumerate(glob.glob(self.mask_folder_name+ "/*" +pattern)):
                image_gray = np.load(image_path, allow_pickle=True)
                # ラベルチェック＆色付き画像の保存
                if self.check_label_num == 1:
                    # 開始
                    #start_time = time.perf_counter()
                    label_list,numpy_image = self.inv_label(image_gray)
                    self.label_data.append(label_list)
                    
                    # 修了
                    end_time = time.perf_counter()
                    # 経過時間を出力(秒)
                    elapsed_time = end_time - start_time
                    print(elapsed_time)
                    #image_color = self.mask_color_change(label_list, image_gray)
                
                    pil_image = Image.fromarray(image_color)
                    image_resize = pil_image.resize(
                        (int(self.canvas.winfo_height() *3/4 ), int(self.canvas.winfo_height() / 2)))
                    numpy_image = np.array(image_resize)
                    
                    data_expanded = np.expand_dims(numpy_image, axis=0)
                    datas.append(data_expanded)
                    self.progress_bar.configure(value=i)
                    self.progress_bar.update()
                # マスク画像保存
                else:
                    pil_image = Image.fromarray(image_gray)
                    #image_resize = ImageOps.pad(pil_image, (self.canvas.winfo_width(), int(self.canvas.winfo_height()/2)))
                    image_resize = pil_image.resize(
                        (int(self.canvas.winfo_height() * 3 / 4 ), int(self.canvas.winfo_height() / 2)))
                    numpy_image = np.array(image_resize)
                    data_expanded = np.expand_dims(numpy_image, axis=0)
                    datas.append(data_expanded)
                self.progress_bar.configure(value=i)
                self.progress_bar.update()
                self.label1_progress["text"] = "mask画像　読み込み中"
                self.label2_progress["text"] = str(i)+"/"+str(self.total_number)
            # (n_samples,height,width,channels)
            images_data = np.concatenate(datas, axis=0)
            self.label1_progress["text"] = ""
            self.label2_progress["text"] = ""
            self.progress_bar.configure(value=0)
            return images_data
            """


    # yaw_degreeの取得 真北に対して 0~180 0~-180の範囲で指定
    def get_uav_azimuth(self,file):
        f = file
        fd = open(f, 'rb')
        d = fd.read()
        xmp_start = d.find(b'<x:xmpmeta')
        xmp_end = d.find(b'</x:xmpmeta')
        xmp_str = d[xmp_start:xmp_end + 12].decode('utf-8')
        # print(xmp_str)
        root = ET.fromstring(xmp_str)
        subroot = root[0][0]
        # yaw_degreeの取得 真北に対して 0~180 0~-180の範囲で指定
        gimbal_yaw_degree = float(subroot.attrib['{http://www.dji.com/drone-dji/1.0/}GimbalYawDegree'])

        return gimbal_yaw_degree

    def get_image_gps(self,img):
        exif = {}

        # exifの取得
        if img._getexif():
            for k, v in img._getexif().items():
                if k in ExifTags.TAGS:
                    exif[ExifTags.TAGS[k]] = v
        lat_tuple = exif['GPSInfo'][2]
        lng_tuple = exif['GPSInfo'][4]
        # 10進数緯度経度
        return self.decimal_latlng(lat_tuple, lng_tuple)

    def decimal_latlng(self, lat_tuple, lng_tuple):
        lat = lat_tuple[0] + (lat_tuple[1] / 60.0) + (lat_tuple[2] / 3600)
        lng = lng_tuple[0] + (lng_tuple[1] / 60.0) + (lng_tuple[2] / 3600)
        return [lat, lng]


def main():
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()



if __name__ == '__main__':
    main()

