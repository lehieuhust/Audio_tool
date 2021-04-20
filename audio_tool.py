import os
import sys
import shutil
import time
import threading
import speech_recognition as sr
from sys import exit
from pathlib import Path
from functools import partial
from pydub import AudioSegment
from pydub.silence import split_on_silence
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QMessageBox,
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

TEXT_FILE_DIR = 'text_file'
google_recognition = sr.Recognizer()

def speed_change(path, speed):
    audio_split_file = AudioSegment.from_file(path)
    sound_with_altered_frame_rate = audio_split_file._spawn(audio_split_file.raw_data, overrides={
        "frame_rate": int(audio_split_file.frame_rate * speed)
    })

    slow_audio = path.replace(".mp3", "_modi.mp3")
    print(slow_audio)
    sound_with_altered_frame_rate.export(slow_audio, format="mp3")
    print(f"Slowdown audio file: {slow_audio}")
    return slow_audio

class audio_convert(QObject):
    finished = pyqtSignal()
    update_progress = pyqtSignal(int, int, str, str, str)
    update_error = pyqtSignal(int)
    
    def audio_to_text(self, audio_file_list, speed_ms, lang_encode):
        percentage_audio = 0
        percentage_file = 0
        per_file = "0/0"
        audio_file_cnt = 0
        audio_total_file = len(audio_file_list)
        print(f"[audio_to_text] audio_file_list:  {audio_file_list}")
        print(f"[audio_to_text] Tốc độ dịch: {speed_ms}ms")
        self.update_progress.emit(0, 0, "0/0", "", "")
        if not audio_file_list:
            print("[audio_to_text] Bạn đã chưa chọn files audio")
            return
        
        for audio_file in audio_file_list:
            audio_file_cnt += 1
            song = AudioSegment.from_mp3(audio_file)
            chunks = split_on_silence(song,
                                      min_silence_len=speed_ms,
                                      silence_thresh=-50)
            
            recog_file_name = audio_file.replace(".mp3", ".txt")
            recog_file = open(recog_file_name, "w+", encoding="utf-8")

            if os.path.exists('audio_chunks'):
                shutil.rmtree('audio_chunks')
            
            try:
                os.mkdir('audio_chunks')
            except FileExistsError:
                pass
            
            os.chdir('audio_chunks')
            chunk_cnt = 0
            percentage_file = round((audio_file_cnt/audio_total_file) * 100)
            per_file = f"{audio_file_cnt}/{audio_total_file}"

            # process each chunk
            for chunk in chunks:
                # Create 0.25 seconds silence chunk
                chunk_silent = AudioSegment.silent(duration=500)
                audio_chunk = chunk_silent + chunk + chunk_silent
                audio_chunk.export("./chunk{0}.wav".format(chunk_cnt), bitrate='192k', format="wav")
                chunk_cnt += 1
            
            chunks.clear()
            del chunks
            
            for idx in range(0, chunk_cnt):
                filename = 'chunk' + str(idx) + '.wav'
                with sr.AudioFile(filename) as source:
                    audio_listened = google_recognition.listen(source)

                try:
                    rec = google_recognition.recognize_google(audio_listened, language=lang_encode)
                    recog_file.write(rec + " ")
                # catch any errors.
                except sr.UnknownValueError:
                    print("Could not understand audio")
                except sr.RequestError as e:
                    print("Could not request results. check your internet connection")
                    self.update_error.emit(1)
                    self.finished.emit()
                    return
                
                percentage_audio = round(((idx + 1)/chunk_cnt) * 100)
                if audio_file_cnt > 1:
                    percent_file = round(((audio_file_cnt - 1)/audio_total_file) * 100) + round(percentage_audio/audio_total_file)
                else:
                    percent_file = round((percentage_file * percentage_audio) / 100)
                print(f"Chuyển đổi: {percent_file}% file")
                self.update_progress.emit(percentage_audio, percent_file, per_file, audio_file, recog_file_name)
                if os.path.exists(filename):
                    os.remove(filename)
            
            if os.path.exists('audio_chunks'):
                shutil.rmtree('audio_chunks')

            os.chdir('..')
            print(f"File text: {recog_file_name}")
            recog_file.close()
        
        self.update_error.emit(0)
        self.finished.emit()
    

class Ui_Form(object):
    def setupUi(self, Form):
        self.lang_select_cnt = False
        self.speed_select_cnt = False
        self.lang_encode = ""
        self.speed_ms = 0
        self.audio_file_list = []

        Form.setObjectName("Form")
        Form.resize(527, 477)
        font = QtGui.QFont()
        font.setPointSize(9)
        Form.setFont(font)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(".\\audio.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Form.setWindowIcon(icon)
        self.horizontalLayout = QtWidgets.QHBoxLayout(Form)
        self.horizontalLayout.setObjectName("horizontalLayout")

        self.msgBox = QtWidgets.QMessageBox(Form)

        self.label_select_lang = QtWidgets.QLabel(Form)
        self.label_select_lang.setGeometry(QtCore.QRect(60, 30, 110, 30))
        self.label_select_lang.setObjectName("label_select_lang")
        self.comboBox_lang = QtWidgets.QComboBox(Form)
        self.comboBox_lang.setGeometry(QtCore.QRect(190, 30, 161, 30))
        self.comboBox_lang.setObjectName("comboBox_lang")
        self.comboBox_lang.addItem("")
        self.comboBox_lang.addItem("")
        self.btn_finish_select_lang = QtWidgets.QPushButton(Form)
        self.btn_finish_select_lang.setGeometry(QtCore.QRect(390, 30, 80, 30))
        self.btn_finish_select_lang.setObjectName("btn_finish_select_lang")
        self.btn_finish_select_lang.clicked.connect(self.finish_select_lang)

        self.label_select_speed = QtWidgets.QLabel(Form)
        self.label_select_speed.setGeometry(QtCore.QRect(60, 80, 115, 30))
        self.label_select_speed.setObjectName("label_select_speed")
        self.comboBox_speed = QtWidgets.QComboBox(Form)
        self.comboBox_speed.setGeometry(QtCore.QRect(190, 80, 161, 30))
        self.comboBox_speed.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
        self.comboBox_speed.setObjectName("comboBox_speed")
        self.comboBox_speed.addItem("")
        self.comboBox_speed.addItem("")
        self.comboBox_speed.addItem("")
        self.btn_finish_select_speed = QtWidgets.QPushButton(Form)
        self.btn_finish_select_speed.setGeometry(QtCore.QRect(390, 80, 80, 30))
        self.btn_finish_select_speed.setObjectName("btn_finish_select_speed")
        self.btn_finish_select_speed.clicked.connect(self.finish_select_speed)

        self.label_select_audio_file = QtWidgets.QLabel(Form)
        self.label_select_audio_file.setGeometry(QtCore.QRect(60, 130, 115, 30))
        self.label_select_audio_file.setObjectName("label_select_audio_file")
        self.btn_select_audio_file = QtWidgets.QPushButton(Form)
        self.btn_select_audio_file.setGeometry(QtCore.QRect(190, 130, 131, 30))
        self.btn_select_audio_file.setObjectName("btn_select_audio_file")
        self.btn_select_audio_file.clicked.connect(self.browse_audio_files)

        self.btn_start_convert = QtWidgets.QPushButton(Form)
        self.btn_start_convert.setGeometry(QtCore.QRect(370, 130, 101, 30))
        self.btn_start_convert.setObjectName("btn_start_convert")
        self.btn_start_convert.clicked.connect(self.start_convert_audio)

        self.label_converting_file = QtWidgets.QLabel(Form)
        self.label_converting_file.setGeometry(QtCore.QRect(60, 180, 110, 30))
        self.label_converting_file.setObjectName("label_converting_file")
        self.text_audio_file = QtWidgets.QLineEdit(Form)
        self.text_audio_file.setGeometry(QtCore.QRect(190, 180, 281, 30))
        self.text_audio_file.setReadOnly(True)
        self.text_audio_file.setObjectName("text_audio_file")

        self.label_convert_progress = QtWidgets.QLabel(Form)
        self.label_convert_progress.setGeometry(QtCore.QRect(60, 230, 80, 30))
        self.label_convert_progress.setObjectName("label_convert_progress")
        self.progressBar_audio = QtWidgets.QProgressBar(Form)
        self.progressBar_audio.setGeometry(QtCore.QRect(190, 230, 281, 30))
        self.progressBar_audio.setProperty("value", 0)
        self.progressBar_audio.setAlignment(QtCore.Qt.AlignCenter)
        self.progressBar_audio.setObjectName("progressBar_audio")

        self.label_file_progress = QtWidgets.QLabel(Form)
        self.label_file_progress.setGeometry(QtCore.QRect(60, 280, 115, 30))
        self.label_file_progress.setObjectName("label_file_progress")
        self.progressBar_file = QtWidgets.QProgressBar(Form)
        self.progressBar_file.setGeometry(QtCore.QRect(190, 280, 281, 30))
        self.progressBar_file.setProperty("value", 0)
        self.progressBar_file.setAlignment(QtCore.Qt.AlignCenter)
        self.progressBar_file.setObjectName("progressBar_file")

        self.label_saving_text_file = QtWidgets.QLabel(Form)
        self.label_saving_text_file.setGeometry(QtCore.QRect(60, 330, 120, 30))
        self.label_saving_text_file.setObjectName("label_saving_text_file")
        self.text_file = QtWidgets.QLineEdit(Form)
        self.text_file.setGeometry(QtCore.QRect(190, 330, 281, 30))
        self.text_file.setReadOnly(True)
        self.text_file.setObjectName("text_file")

        self.label_debug = QtWidgets.QLabel(Form)
        self.label_debug.setGeometry(QtCore.QRect(10, 450, 55, 16))
        self.label_debug.setText("")
        self.label_debug.setObjectName("label_debug")

        self.btn_exit = QtWidgets.QPushButton(Form)
        self.btn_exit.setGeometry(QtCore.QRect(380, 385, 93, 30))
        self.btn_exit.setObjectName("btn_exit")
        self.btn_exit.clicked.connect(exit)

        self.retranslateUi(Form)
        self.comboBox_speed.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Audio to text"))
        self.btn_finish_select_lang.setText(_translate("Form", "OK"))
        self.comboBox_lang.setItemText(0, _translate("Form", "Tiếng Việt"))
        self.comboBox_lang.setItemText(1, _translate("Form", "English"))
        self.label_select_lang.setText(_translate("Form", "Chọn ngôn ngữ:"))
        self.btn_finish_select_speed.setText(_translate("Form", "OK"))
        self.comboBox_speed.setItemText(0, _translate("Form", "Chậm"))
        self.comboBox_speed.setItemText(1, _translate("Form", "Bình thường"))
        self.comboBox_speed.setItemText(2, _translate("Form", "Nhanh"))
        self.label_select_speed.setText(_translate("Form", "Chọn tốc độ dịch:"))
        self.btn_start_convert.setText(_translate("Form", "Bắt đầu"))
        self.btn_select_audio_file.setText(_translate("Form", "Chọn file"))
        self.label_select_audio_file.setText(_translate("Form", "Chọn mp3 file:"))
        self.btn_exit.setText(_translate("Form", "Thoát"))
        self.label_converting_file.setText(_translate("Form", "Đang dịch file:"))
        self.label_file_progress.setText(_translate("Form", "Số file đang dịch:"))
        self.label_saving_text_file.setText(_translate("Form", "Đang lưu vào file:"))
        self.progressBar_file.setFormat(_translate("Form", "%p/%p"))
        self.label_convert_progress.setText(_translate("Form", "Dịch xong:"))
    
    def finish_select_lang(self):
        print (f"Bạn chọn ngôn ngữ: {self.comboBox_lang.currentText()}")
        self.lang_select_cnt = True
        if self.comboBox_lang.currentText() == "Tiếng Việt":
            self.lang_encode = "vi-VN"
        elif self.comboBox_lang.currentText() == "English":
            self.lang_encode = "en-US"
        return self.lang_encode
    
    def finish_select_speed(self):
        print (f"Bạn chọn tốc độ dịch: {self.comboBox_speed.currentText()}")
        self.speed_select_cnt = True
        if self.comboBox_speed.currentText() == "Chậm":
            print("Tốc độ dịch - Chậm")
            self.speed_ms = 850
        elif self.comboBox_speed.currentText() == "Bình thường":
            print("Tốc độ dịch - Bình thường")
            self.speed_ms = 450
        elif self.comboBox_speed.currentText() == "Nhanh":
            print("Tốc độ dịch - Nhanh")
            self.speed_ms = 100
        return self.speed_ms
    
    def browse_audio_files(self):
        home_dir = str(Path.home())
        self.audio_file_list, _ = QtWidgets.QFileDialog.getOpenFileNames(parent=Form, caption='Select File', directory=home_dir, filter="Audio files (*.mp3 *.mp4)")
    
    def show_err(self, err_text):
        self.msgBox.setIcon(QMessageBox.Critical)
        self.msgBox.setWindowTitle("Lỗi")
        self.msgBox.setText(err_text)
        self.msgBox.exec()
    
    def show_info(self, info_text):
        self.msgBox.setIcon(QMessageBox.Information)
        self.msgBox.setWindowTitle("Info")
        self.msgBox.setText(info_text)
        self.msgBox.exec()
    
    def update_err(self, err):
        if err == 1:
            self.show_err("Lỗi kết nối mạng. Hãy thử lại sau !!!")
        elif err == 0:
            self.show_info("Đã chuyển đổi xong file audio")
            self.label_converting_file.setText("Đã dịch xong:")
            self.label_saving_text_file.setText("Đã lưu xong:")
    
    def update_bar(self, percent_audio, percent_file, per_file, audio_file, op_text_file):
        # print (f"Chuyển đổi audio: {percent_audio}%")
        # print (f"Chuyển đổi file: {percent_file}%")
        # print (f"Audio file: {audio_file}")
        # print (f"Text file: {op_text_file}")

        self.text_audio_file.setText(audio_file)
        self.text_audio_file.setCursorPosition(0)

        self.text_file.setText(op_text_file)   
        self.text_file.setCursorPosition(0)

        self.progressBar_audio.setValue(percent_audio)

        self.progressBar_file.setValue(percent_file)
        self.progressBar_file.setFormat(per_file)


    def start_convert_audio(self):
        print ("Start convert audio file")
        if self.lang_select_cnt == False:
            self.show_err("Bạn chưa chọn ngôn ngữ !!!")
            return
        if self.speed_select_cnt == False:
            self.show_err("Bạn chưa chọn tốc độ dịch !!!")
            return
        if not self.audio_file_list:
            self.show_err("Bạn chưa chọn file audio !!!")
            return

        self.btn_finish_select_lang.setEnabled(False)
        self.btn_finish_select_speed.setEnabled(False)
        self.btn_select_audio_file.setEnabled(False)
        self.btn_start_convert.setEnabled(False)

        self.thread = QThread()
        self.worker = audio_convert()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(partial(self.worker.audio_to_text, self.audio_file_list, self.speed_ms, self.lang_encode))
        self.worker.update_progress.connect(self.update_bar)
        self.worker.update_error.connect(self.update_err)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

        self.thread.finished.connect(
            lambda: self.audio_file_list.clear()
        )
        self.thread.finished.connect(
            lambda: self.btn_finish_select_lang.setEnabled(True)
        )
        self.thread.finished.connect(
            lambda: self.btn_finish_select_speed.setEnabled(True)
        )
        self.thread.finished.connect(
            lambda: self.btn_select_audio_file.setEnabled(True)
        )
        self.thread.finished.connect(
            lambda: self.btn_start_convert.setEnabled(True)
        )
    

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())
