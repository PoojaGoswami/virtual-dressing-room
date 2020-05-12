import sys
import os
import cv2
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QThread, Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QLabel, QApplication, QFileDialog, QListWidgetItem
from PyQt5.QtGui import QImage, QIcon, QPixmap
from design import Ui_MainWindow
import TranparentOverlay
import time
from queue import Queue


#load pretrained face detection classifier
face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")


class Thread(QThread):
    changePixmap = pyqtSignal(QImage)


g_video_state = ["Stop"]
g_video_source = ["File"]


# class ImageLoader(QThread):
#     changePixmap = pyqtSignal(QImage)
#
#     def listwidgetclicked(self, item):
#         idx = id(item)
#         print('video class member', VideoThread.shirt_img)
#         print('click {}'. format(idx), self.cv_images[idx].image)
#         VideoThread.shirt_img = self.cv_images[idx].image
#
#     def __init__(self, image_cache):
#         super(ImageLoader, self).__init__()
#         self.cv_images = {}
#
#         # ControlWindow.ui.image_feed.itemClicked.connect(self.listwidgetclicked)
#
#     def load_image(self, queue_item):
#         image_path = queue_item[0]
#         size = queue_item[1]
#         # if not (image_path in self.image_cache):
#         pixmap = QPixmap(image_path).scaled(250, 250, Qt.KeepAspectRatio)  # Actual Image Loading
#         # self.image_cache[image_path] = pixmap
#
#     def run(self):
#         while True:
#             time.sleep(0.1)  # <- Added delay
#             current_item = self.queue.get()
#             if current_item:
#                 self.load_image(current_item)
#             else:
#                 break
#
#     def add_to_queue(self, image_path, size):
#         item = [image_path, size]
#         self.queue.put(item)


class VideoThread(QThread):
    def __init__(self):
        super(VideoThread, self).__init__()
        self.shirt_img = None

    changePixmap = pyqtSignal(QImage)
    changePixmap2 = pyqtSignal(QImage)

    change_theta1 = pyqtSignal(float)
    change_theta2 = pyqtSignal(float)
    change_video_state = pyqtSignal(str)

    def run(self):

        print('self.shirt_img', self.shirt_img)
        global g_video_state
        global g_video_source
        self.video_state = "Playing"
        print('g_video_source', g_video_source)

        if g_video_source[0] is "Camera":
            cap = cv2.VideoCapture(0)
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            frame_width = int(cap.get(3))
            frame_height = int(cap.get(4))
            size = (frame_width, frame_height)
            fps = 20
            out = cv2.VideoWriter("output.avi", fourcc, fps, size)

        elif g_video_source[0] is "File":

            #self.vid_path = "test2.mp4"
            cap = cv2.VideoCapture(self.vid_path)

        if not cap.isOpened():
            print("Error opening video stream or file")

        print(self.video_state)

        while True:
            print('self.shirt_img run', self.shirt_img)
            if self.video_state == "Stop":
                break
            ret, frame = cap.read()

            if ret:
                if g_video_source[0] is "File": frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                faces = face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )


                # Draw a rectangle around the faces
                faces = sorted(faces, key=lambda x: -1*x[2] * x[3])
                print(faces)
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                    scale = 0.40

                    if self.shirt_img is not None:

                        w_, h_ = self.shirt_img.shape[:2]
                        scale = (h * 3.5) / w_
                        scale = round(scale*20)
                        scale = round(scale/20, 2)

                        w_, h_ = int(w_ * scale), int(h_ * scale)

                        cx, cy = (x + w // 2), y + h + h//5
                        cv2.circle(frame, (cx, cy), 5, (255, 0, 0), 2)

                        dx, dy = cx - w_ // 2, cy + h // 3
                        cv2.circle(frame, (dx, dy), 5, (255, 0, 0), 3)
                        zx, zy = cx + w_ // 2, cy + h // 3
                        cv2.circle(frame, (zx, zy), 5, (0, 255, 0), 3)

                        frame = TranparentOverlay.transparentOverlay(frame, self.shirt_img,
                                                                 pos=(cx, cy),
                                                                 scale=scale)
                    break
                rgbImage1 = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                h, w, ch = rgbImage1.shape
                bytesPerLine = ch * w
                convertToQtFormat = QImage(rgbImage1.data, w, h, bytesPerLine, QImage.Format_RGB888)
                p2 = convertToQtFormat.scaled(1000, 1000, Qt.KeepAspectRatio)

                self.changePixmap.emit(p2)
                time.sleep(0.05)
            else:
                break

        print("Cap released")
        cap.release()
        self.video_state = "Stop"
        self.change_video_state.emit(self.video_state)


# try:
#     _fromUtf8 = QtCore.QString.fromUtf8
# except AttributeError:
#     _fromUtf8 = lambda s: s

class ControlWindow:

    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self.MainWindow = QtWidgets.QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.MainWindow)
        self.cv_images = {}

        self.load_images()

        self.video_thread = VideoThread()
        self.video_thread.changePixmap.connect(lambda p: self.setVideoImage(p))
        self.video_thread.change_video_state.connect(lambda s: self.update_video_state(s))

        self.ui.video_play_button.clicked.connect(self.play_video)
        #self.ui.video_pause_button.clicked.connect(self.pause_video)
        self.ui.load_video_button.clicked.connect(lambda s: self.load_video("File"))
        self.ui.video_stop_button.clicked.connect(self.stop_video)

        self.ui.load_web_cam_button.clicked.connect(lambda s: self.load_video("Camera"))
        self.ui.image_feed.itemClicked.connect(self.listwidgetclicked)


    def listwidgetclicked(self, item):
        idx = id(item)
        print('video class member',self.video_thread.shirt_img)
        print('click {}'. format(idx), self.cv_images[idx].image)
        self.video_thread.shirt_img = self.cv_images[idx].image

    def load_images(self):
        path = "tshirt/"
        included_extensions = ['jpg', 'jpeg', 'bmp', 'png', 'gif']
        file_names = [fn for fn in os.listdir(path)
                      if any(fn.endswith(ext) for ext in included_extensions)]

        # shirt_img = self.load_shirt("tshirt/shirt1.png")

        self.cv_images = {}

        for i in file_names:
            image = self.load_shirt(path+i)
            item = QListWidgetItem()
            icon = QtGui.QIcon()
            # icon.addPixmap(QtGui.QPixmap(_fromUtf8(path+i)), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            icon.addPixmap(QtGui.QPixmap(path + i), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            item.setIcon(icon)
            self.cv_images[id(item)] = CvImages(path + i, image)
            self.ui.image_feed.addItem(item)

        #print('cv', self.cv_images)

    def load_shirt(self, img_path):
        img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)

        assert img.shape[2] == 4, "shirt image : {} doesn't have alpha channel".format(img_path)
        alpha_channel = img[:, :, -1]

        # calculate extreme points of shirt
        x, y, w, h = cv2.boundingRect(alpha_channel)

        return img[y:y + h, x:x + w]

    def setVideoImage(self, p):
        p = QPixmap.fromImage(p)
        p = p.scaled(1200, 1200, Qt.KeepAspectRatio)
        self.ui.video_feed1.setPixmap(p)

    def setVideoOutput(self, p):
        p = QPixmap.fromImage(p)
        p = p.scaled(1000, 1000, Qt.KeepAspectRatio)
        self.ui.video_feed2.setPixmap(p)

    def load_video(self, video_source):
        global g_video_source
        if video_source == "Camera":
            g_video_source[0] = "Camera"
            self.ui.video_path_label.setText('')
            self.video_thread.start()
        else:
            g_video_source[0] = "File"

            options = QFileDialog.Options()
            fileName, _ = QFileDialog.getOpenFileName(self.MainWindow, "QFileDialog.getOpenFileName()", os.getcwd(),
                                                      "All Files (*);;Avi Files (*.avi)", options=options)
            if fileName:
                self.ui.video_path_label.setText(fileName)
                self.video_thread.vid_path = fileName
                self.play_video()

    def run(self):
        self.MainWindow.show()
        sys.exit(self.app.exec_())

    def play_video(self):
        self.video_thread.vid_path = self.ui.video_path_label.text()
        self.video_thread.start()
        self.ui.video_play_button.setEnabled(False)

    def pause_video(self):
        global g_video_state
        if g_video_state[0] == "Paused":
            g_video_state[0] = "Playing"
        else:
            g_video_state[0] = "Paused"

    def stop_video(self):
        g_video_state[0] = "Stop"
        self.video_thread.video_state = "Stop"
        self.ui.video_play_button.setEnabled(True)

    def update_video_state(self, state):
        #print ("Update state", state)
        if state == "Stop":
            self.stop_video()


class CvImages:
    def __init__(self, img_path, image):
        self.img_path = img_path
        self.image = image


if __name__ == "__main__":
    ui = ControlWindow()
    ui.run()
