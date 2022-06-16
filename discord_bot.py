import requests
import json
import datetime

WEBHOOK_URL = 'https://discord.com/api/webhooks/986488553225732108/bzLE4T34S4nVFvFj-Gpom-F6Y6b36XwR07q2dFg33-8QGm2Zx2OeGTFfsPaTI65sf6kf'

def send_capture(_filepath, _filename):
       
   dt_now = datetime.datetime.now()
   datestr = (dt_now.strftime('%Y-%m-%d %H:%M:%S'))
   main_content = {
      "username": "監視カメラ",
      "content": datestr
   }

   ### 画像添付
   with open( _filepath+_filename, 'rb' ) as f:
      file_bin = f.read()
   files_capture = {
      "favicon" : ( _filename, file_bin),
   }
   res = requests.post( WEBHOOK_URL, main_content, files = files_capture )