import os
import numpy as np
import pandas as pd
import glob
from PIL import Image, ImageTk, ImageOps
import PIL.ExifTags as ExifTags
import xml.etree.ElementTree as ET
from tqdm import tqdm

# yaw_degreeの取得 真北に対して 0~180 0~-180の範囲で指定
def get_uav_azimuth(file):
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

def get_image_gps(img):
    exif = {}

    # exifの取得
    if img._getexif():
        for k, v in img._getexif().items():
            if k in ExifTags.TAGS:
                exif[ExifTags.TAGS[k]] = v
    lat_tuple = exif['GPSInfo'][2]
    lng_tuple = exif['GPSInfo'][4]
    # 10進数緯度経度
    return decimal_latlng(lat_tuple, lng_tuple)

def decimal_latlng(lat_tuple, lng_tuple):
    lat = lat_tuple[0] + (lat_tuple[1] / 60.0) + (lat_tuple[2] / 3600)
    lng = lng_tuple[0] + (lng_tuple[1] / 60.0) + (lng_tuple[2] / 3600)
    return [lat, lng]

def get_save_folder_path(path):  #フォルダ名が重複していてもできる
    folder = os.path.basename(os.path.dirname(os.path.dirname(path)))
    path=path[::-1]
    save_folder="save_folder"
    path.replace(folder[::-1],save_folder[::-1],1)
    path = path[::-1]
    return path

def inv_label(mask_img):
    label=[]
    color = [[255, 0, 0], [255, 165, 0], [255, 255, 0], [173, 255, 47], [0, 128, 0], [102, 205, 170],
                  [135, 206, 235], [0, 0, 255], [128, 0, 128]]
    # ["赤","オレンジ","黄色","黄緑","緑","青緑","水色","青","紫"]
    # 画像のリサイズ(appのキャンバスの大きさから指定(縦横比が2：3))
    width = 549 * 3 / 4  # canvas_height=549
    height = 549 / 2
    plus_image=np.zeros((int(height), int(width),3))
    label_order=0
    for i in range(1,91):
        a=(mask_img==i)
        if a.any():
            label.append(i)
            pil_image = Image.fromarray(a)
            image_resize = pil_image.resize((int(width), int(height)))
            numpy_image = np.array(image_resize)
            color_img = [color[label_order][0], color[label_order][1],
                         color[label_order][2]] * np.stack([numpy_image, numpy_image, numpy_image], 2)
            plus_image += color_img
            label_order += 1
    return label,plus_image.astype(np.uint8)

def read_image(path):
    gps_lat_list = []
    gps_lng_list = []
    gimbal_degree_list = []
    label_list=[]
    # 画像のリサイズ(appのキャンバスの大きさから指定(縦横比が2：3))
    width = 549 * 3 / 4  # canvas_height=549
    height = 549 / 2  # canvas_width=681
    #パスの取得
    original_folder_name=path
    mask_folder_name = os.path.join(path, "mask")
    folder=os.path.basename(os.path.dirname(os.path.dirname(original_folder_name)))
    save_original_folder_path=original_folder_name.replace(folder,"save_folder")
    save_mask_folder_path = os.path.join(save_original_folder_path, "mask")
    #フォルダの作成
    os.makedirs(save_original_folder_path,exist_ok=True)
    os.makedirs(save_mask_folder_path, exist_ok=True)
    # original画像の処理
    for image_path in glob.glob(os.path.join(original_folder_name,"*.JPG")):
        pil_image = Image.open(image_path)
        # ドローンの角度を取得するための処理
        gimbal_yaw_degree = get_uav_azimuth(image_path)
        gimbal_degree_list.append(gimbal_yaw_degree)
        # 撮影画像中心のGPS座標を取得
        latlng = get_image_gps(pil_image)
        gps_lat_list.append(latlng[0])
        gps_lng_list.append(latlng[1])
        #画像のリサイズ
        image_resize = pil_image.resize((int(width), int(height)))
        #.JPGで保存
        image_resize.save(os.path.join(save_original_folder_path,os.path.basename(image_path)))

    #mask画像の処理
    for image_path in glob.glob(mask_folder_name + "/*.npy"):
        image_gray = np.load(image_path, allow_pickle=True)
        label, numpy_image = inv_label(image_gray)
        np.save(os.path.join(save_mask_folder_path,os.path.basename(image_path)),numpy_image)
        label_list.append(label)
    #gps,gimbal_degree,labelをdfに変換
    df=pd.DataFrame(data={"gps_lat":gps_lat_list,
                          "gps_lng":gps_lng_list,
                          "degree":gimbal_degree_list})
    df_label=pd.DataFrame(data={"label":label_list})
    return df, df_label

def get_path(data_path):
    path_list=[]
    date_folders = glob.glob(os.path.join(data_path,"*"))
    for date_folder in date_folders:  #日付フォルダのパス取得
        if "." in date_folder:   #何かファイルが混ざっていた場合スキップ
            continue
        height_folders = glob.glob(os.path.join(date_folder, "*"))
        for height_folder in height_folders:  #高さフォルダのパス取得
            height_folder_name = os.path.basename(height_folder)
            if "." in height_folder_name:  # 何かファイルが混ざっていた場合スキップ
                continue
            if "8" in height_folder_name or "10" in height_folder_name or "12" in height_folder_name:  #高さの含んだフォルダのみ取得
                path_list.append(height_folder)
    return path_list

def get_filenames(path):
    original_filename_list=[]
    mask_filename_list=[]
    original_filename_paths = glob.glob(os.path.join(path,"*.JPG"))
    mask_folder_path = os.path.join(path, "mask")
    mask_filename_paths = glob.glob(os.path.join(mask_folder_path, "*.npy"))

    for original_filename_path in original_filename_paths:
        original_filename_list.append(os.path.splitext(os.path.basename(original_filename_path))[0])  # 拡張子を削除
    for mask_filename_path in mask_filename_paths:
        mask_filename_list.append(os.path.splitext(os.path.basename(mask_filename_path))[0])  # 拡張子を削除

    #dfの作成(画像名＆maskの有無(有1無0))
    original_df = pd.DataFrame(np.zeros(len(original_filename_list)),
                           columns=["org_inf"],
                           index=original_filename_list)
    mask_df = pd.DataFrame(np.ones(len(mask_filename_list)),
                           columns=["mask_inf"],
                           index=mask_filename_list)
    df = pd.merge(original_df, mask_df, how='outer', left_index=True, right_index=True)
    df = df.fillna(0)
    df = df.drop("org_inf", axis=1)
    return df,mask_filename_list

def main():
    data_path = "D:\\マイ ノートパソコン\\ドキュメント\\授業用フォルダー\\4年\\延原研\\圃場app\\field_segmentation"  #ここに処理したいフォルダのおおもとのパスを入力
    path_list = get_path(data_path)
    folder = os.path.basename(data_path)
    for path in tqdm(path_list,desc="original&mask_processing"):
        original_folder_name = path
        mask_folder_name = os.path.join(path, "mask")
        df1,mask_filename_list = get_filenames(original_folder_name)  #画像名＆maskの有無(有1無0)
        df2,df_label=read_image(original_folder_name)  #gps_lat,gps_lng,degreeのdf　と　labelのdf
        df_label.index = mask_filename_list
        df2.index = df1.index
        df=pd.merge(df1,df2,how="left",left_index=True,right_index=True)
        df = pd.merge(df, df_label, how='outer', left_index=True, right_index=True)
        save_csv_path = os.path.join(original_folder_name.replace(folder, "save_folder"),"inf.csv")
        df.to_csv(save_csv_path)

if __name__ == '__main__':
    main()