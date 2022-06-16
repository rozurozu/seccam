import cv2
import datetime
import threading
import os
import shutil
import time
import configparser

import discord_bot

#保存先のディレクトリ
REC_DIR = '/home/waduhek/work/seccam/out/'
#デバイスIDの設定
CAMID1 = 0
CAMID2 = 2
MICID = 6
#カメラの設定
WIDTH = 640
HEIGHT = 480
# configファイルの読み込み
inifile=configparser.ConfigParser()
inifile.read('config.ini')
FPS = int(inifile['DEFAULT']['fps'])
REC_TIME = int(inifile['DEFAULT']['rec_time'])

# mode 0,1,9 OFF,ON,quit
# OFFで初期化
u1g_xmode = 0

#-------------------------------
def cam_set(DEVICE_ID,WIDTH,HEIGHT,FPS):
    # video capture
    cap = cv2.VideoCapture(DEVICE_ID)

    # フォーマット・解像度・FPSの設定
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, FPS)

    # # フォーマット・解像度・FPSの取得
    # fourcc = decode_fourcc(cap.get(cv2.CAP_PROP_FOURCC))
    # width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    # height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    # fps = cap.get(cv2.CAP_PROP_FPS)
    # print("ID:{} fourcc:{} fps:{}　width:{}　height:{}".format(DEVICE_ID, fourcc, fps, width, height))

    return cap
#-------------------------------
# def decode_fourcc(v):
#         v = int(v)
#         return "".join([chr((v >> 8 * i) & 0xFF) for i in range(4)])
#-------------------------------
def motion_detect( _frame, _before):
    before = _before # 前回の画像を保存する変数

    # 白黒画像に変換
    gray = cv2.cvtColor(_frame, cv2.COLOR_BGR2GRAY)

    if before is None:
        before = gray.astype("float")
        return 0, before
    #現在のフレームと移動平均との差を計算
    cv2.accumulateWeighted(gray, before, 0.8) #値を小さくすると感度がよくなる。0.5だと感度よすぎた。
    frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(before))
    #frameDeltaの画像を２値化
    thresh = cv2.threshold(frameDelta, 3, 255, cv2.THRESH_BINARY)[1]
    #輪郭のデータを得る
    contours = cv2.findContours(thresh,
                    cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_SIMPLE)[0]

    # 差分があったらTRUEを返す
    for target in contours:
        x, y, w, h = cv2.boundingRect(target)
        if w < 30: continue # 小さな変更点は無視
        return 1, before
    return 0, before

#-------------------------------
def capture_movie():
    # グローバル変数の宣言
    global u1g_xmode

    # 変数初期化
    u1t_xdetect = 0 #動体検知フラグ
    u1t_xfilename = 0 #ファイル名決定済みフラグ
    filename = 0
    before = None

    # デバイス設定
    DEVICE_ID = CAMID1
    cap1=cam_set(DEVICE_ID,WIDTH,HEIGHT,FPS)
    DEVICE_ID = CAMID2
    cap2=cam_set(DEVICE_ID,WIDTH,HEIGHT,FPS)

    # 動画の設定
    fourcc=cv2.VideoWriter_fourcc('M','J','P','G')
    #--------------------------------------

    while True:
        # 監視モードON
        if u1g_xmode == 1:
            
            startsec = time.time()
            # カメラ画像取得1
            ret1, frame1 = cap1.read()
            if not ret1:
                print('cam1 not found error')
                break

            # カメラ画像取得2
            ret2, frame2 = cap2.read()
            if not ret2:
                print('cam2 not found error')
                break

            # 画像結合
            im_h=cv2.hconcat([frame1,frame2])

            # 動体検知出来ていないときは、検知処理を実行する。
            if u1t_xdetect == 0:
                u1t_xdetect, before = motion_detect(im_h, before)
            # u1t_xdetect = 1

            if u1t_xdetect == 1:
                print('動体を検知')
                if u1t_xfilename == 0:
                    time_recstart = time.time()
                    dt_now = datetime.datetime.now()
                    filename = (dt_now.strftime('%Y%m%d%H%M%S') + '.avi')
                    u1t_xfilename = 1
                    video=cv2.VideoWriter(REC_DIR+filename,fourcc,FPS,(WIDTH+WIDTH,HEIGHT))
                    # video=cv2.VideoWriter(filename,fourcc,FPS,(WIDTH+WIDTH,HEIGHT))
            
                # 動画ファイル書き込み
                video.write(im_h)
                
                # 動画ファイルのFPSを調整
                print(1/FPS - (time.time()-startsec))
                sleep_secs = 1/FPS - (time.time()-startsec)
                if sleep_secs < 0:  # マイナスになるようなら、FPSはもっと低い値にする
                    print('FPSが高すぎて処理が間に合っていないかも' , sleep_secs , sep=':')
                else:
                    time.sleep(sleep_secs)

                # 30秒数えてファイル分割
                if time.time() - time_recstart > REC_TIME:
                    u1t_xfilename = 0 
                    u1t_xdetect = 0
                    before = None #動体検知用の画像削除
                    discord_bot.send_capture(REC_DIR, filename)
                    os.remove(REC_DIR + filename)
                

        # 監視モードOFF
        if u1g_xmode == 9:
            # VideoCaptureオブジェクト破棄
            cap1.release()
            cap2.release()
            video.release()
            # tmpフォルダの動画全削除
            shutil.rmtree(REC_DIR)
            os.mkdir(REC_DIR)
            break
            
#-------------------------------
def main( ):
    # グローバル変数の宣言
    global u1g_xmode

    thread = threading.Thread(target = capture_movie)
    thread.start()
    print('監視OFFモード')
    time.sleep(2)

    while True:
        print('モードを選択  0:OFF, 1:ON, 9:プログラム終了')
        u1t_xbefmode = u1g_xmode
        u1g_xmode = int(input())
        if u1g_xmode == 0:
            print('監視OFFモード')
        elif u1g_xmode == 1:
            print('監視ONモード')
        elif u1g_xmode == 9:
            print('プログラムを終了します')
            break
        else:
            print('error 再度入力してください')
            u1g_xmode = u1t_xbefmode
    
    thread.join()
    return

#-------------------------------
if __name__ == '__main__':
    main()