# run.py
import os
import threading
import webview

def start_django():
    os.system('python manage.py runserver 127.0.0.1:8000')

if __name__ == '__main__':
    t = threading.Thread(target=start_django)
    t.daemon = True
    t.start()

    webview.create_window("PigFarm System", "http://127.0.0.1:8000")
