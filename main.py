import os
import shutil
import speech_recognition as sr
import threading
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
import tkinter.ttk as ttk
from pydub import AudioSegment
from pydub.silence import split_on_silence

lang_Option = [
    "Tiếng Việt",
    "English"
]

google_recognition = sr.Recognizer()

window = Tk()

label_audio_process = Label(window, text="Chưa chọn file mp3")
label_audio_text = Label(window, text="Chưa lưu vào file text")

audio_prog_bar = ttk.Progressbar(window, style='text.Horizontal.TProgressbar', length=332, maximum=100, value=0)
audio_prog_bar_style = ttk.Style(window)

file_prog_bar = ttk.Progressbar(window, style='green.Horizontal.TProgressbar', length=332)
# file_prog_bar_style = ttk.Style(window)

def update_file_bar(percentage):
    global file_prog_bar
    # global file_prog_bar_style
    file_prog_bar['value'] = percentage
    # file_prog_bar_style.configure(style='green.Horizontal.TProgressbar', text='{:g} %'.format(percentage))

def update_audio_bar(percentage):
    global audio_prog_bar
    global audio_prog_bar_style
    audio_prog_bar['value'] = percentage
    audio_prog_bar_style.configure('text.Horizontal.TProgressbar', text='{:g} %'.format(percentage))

def speed_change(filename, audio_src, speed):
    sound_with_altered_frame_rate = audio_src._spawn(audio_src.raw_data, overrides={
        "frame_rate": int(audio_src.frame_rate * speed)
    })

    slow_audio = filename.replace(".mp3", "_modi.mp3")
    print(slow_audio)
    sound_with_altered_frame_rate.export(slow_audio, format="mp3")
    print(f"Slowdown audio file: {slow_audio}")
    return slow_audio

def audio_to_text(path_list, lang="vi-VN"):
    global label_audio_text
    global label_audio_process
    audio_file_cnt = 0
    audio_total_file = len(path_list)
    print(f"[audio_to_text] Bạn đã chọn {audio_total_file} files audio")
    for audio_file in path_list:
        audio_file_cnt += 1
        song = AudioSegment.from_mp3(audio_file)
        chunks = split_on_silence(song,
                                  min_silence_len=270,
                                  silence_thresh=-47
                                  )

        recog_file_name = audio_file.replace(".mp3", ".txt")
        recog_file = open(recog_file_name, "w+", encoding="utf-8")

        if os.path.exists('audio_chunks'):
            print('Delete audio_chunks folder')
            shutil.rmtree('audio_chunks')

        try:
            os.mkdir('audio_chunks')
        except FileExistsError:
            pass
        
        os.chdir('audio_chunks')
        chunk_cnt = 0
        percentage_file = round((audio_file_cnt/audio_total_file) * 100)
        # process each chunk
        for chunk in chunks:
            # Create 0.5 seconds silence chunk
            chunk_silent = AudioSegment.silent(duration=500)
            audio_chunk = chunk_silent + chunk + chunk_silent
            audio_chunk.export("./chunk{0}.wav".format(chunk_cnt), bitrate='192k', format="wav")
            chunk_cnt += 1
        for idx in range(0, chunk_cnt):
            filename = 'chunk' + str(idx) + '.wav'
            label_audio_process['text'] = "Đang chuyển đổi file audio: " + os.path.basename(audio_file)
            with sr.AudioFile(filename) as source:
                audio_listened = google_recognition.listen(source)

            try:
                rec = google_recognition.recognize_google(audio_listened, language=lang)
                recog_file.write(rec + " ")
            # catch any errors.
            except sr.UnknownValueError:
                print("Could not understand audio")
            except sr.RequestError as e:
                print("Could not request results. check your internet connection")
                messagebox.showerror(title="Lỗi", message="Đường truyền Internet không ổn định !!!")
                return
            label_audio_text['text'] = "Đang ghi vào file text: " + os.path.basename(recog_file_name)
            percentage_audio = round(((idx + 1)/chunk_cnt) * 100)
            update_audio_bar(percentage_audio)
            print(f"Chuyển đổi: {percentage_audio} %")
        os.chdir('..')
        update_file_bar(percentage_file)
        update_audio_bar(0)
        print(f"File text: {recog_file_name}")
        if os.path.exists('audio_chunks'):
            print('Delete audio_chunks folder')
            shutil.rmtree('audio_chunks')
        
    update_file_bar(0)
    label_audio_process['text'] = "Chưa chọn file mp3"
    label_audio_text['text'] = "Chưa lưu vào file text"
    messagebox.showinfo(title="Đã xong", message="Hoàn tất chuyển đổi file audio.")


class tool_gui:
    # global audio_prog_bar
    # global audio_prog_bar_style
    # global file_prog_bar
    # global file_prog_bar_style
    # global label_audio_process
    # global label_audio_text
    def __init__(self, win):
        self.lang_select_cnt = FALSE
        self.lang_encode = ""
        self.audio_file_list = []
        audio_prog_bar_style.layout('text.Horizontal.TProgressbar',
                     [('Horizontal.Progressbar.trough',
                       {'children': [('Horizontal.Progressbar.pbar',
                                      {'side': 'left', 'sticky': 'ns'})],
                        'sticky': 'nswe'}),
                      ('Horizontal.Progressbar.label', {'sticky': ''})])
        audio_prog_bar_style.configure('text.Horizontal.TProgressbar', text='0 %')

        # file_prog_bar_style.layout('text.Horizontal.TProgressbar',
        #              [('Horizontal.Progressbar.trough',
        #                {'children': [('Horizontal.Progressbar.pbar',
        #                               {'side': 'left', 'sticky': 'ns'})],
        #                 'sticky': 'nswe'}),
        #               ('Horizontal.Progressbar.label', {'sticky': ''})])
        # file_prog_bar_style.configure('green.Horizontal.TProgressbar', text='0 %')
        self.lang = StringVar(win)
        self.lang.set(lang_Option[0])
        self.label_select_lang = Label(win, text="Chọn ngôn ngữ: ")
        self.menu_lang = OptionMenu(win, self.lang, *lang_Option)
        self.button_ok = Button(win, text="OK", command=self.finish_select)
        self.label_select_audio = Label(win, text="Chọn mp3 file: ")
        self.button_explore = Button(win, text="Chọn file", command=self.browse_files)
        self.button_convert = Button(win, text="Bắt đầu", command=self.convert_audio)
        self.button_exit = Button(win, text="Thoát", command=exit)
        self.menu_lang.pack()
        self.button_ok.pack()
        audio_prog_bar.pack()
        file_prog_bar.pack()
        self.label_select_lang.place(x=130, y=40)
        self.menu_lang.place(x=260, y=40)
        self.button_ok.place(x=430, y=40)
        self.label_select_audio.place(x=130, y=100)
        self.button_explore.place(x=260, y=100)
        self.button_convert.place(x=400, y=100)
        label_audio_process.place(x=130, y=160)
        audio_prog_bar.place(x=130, y=190)
        label_audio_text.place(x=130, y=230)
        file_prog_bar.place(x=130, y=260)
        self.button_exit.place(x=275, y=330)
        update_audio_bar(0)
        update_file_bar(0)
    
    def finish_select(self):
        self.lang_select_cnt = TRUE
        if self.lang.get() == "Tiếng Việt":
            print(f"Ngôn ngữ chuyển đổi - Tiếng Việt")
            self.lang_encode = "vi-VN"
        elif self.lang.get() == "English":
            print(f"Ngôn ngữ chuyển đổi - Tiếng Anh")
            self.lang_encode = "en-US"
        return self.lang_encode

    def browse_files(self):
        self.audio_file_list = filedialog.askopenfilename(title="Select audio file", multiple=True,
                                                          filetypes=(("Audio files", "*.mp3*"),))
        self.audio_file_list = window.tk.splitlist(self.audio_file_list)
        print(f"File mp3: {self.audio_file_list}")

    def convert_audio(self):
        if self.lang_select_cnt == FALSE:
            print("Bạn chưa chọn ngôn ngữ")
            messagebox.showerror(title="Lỗi", message="Bạn chưa chọn ngôn ngữ !!!")
            return
        if not self.audio_file_list:
            print("Bạn chưa chọn file audio")
            messagebox.showerror(title="Lỗi", message="Bạn chưa chọn file audio !!!")
            return

        self.audio_thread = threading.Thread(target=audio_to_text, args=(self.audio_file_list, self.lang_encode,))
        self.audio_thread.start()


if __name__ == '__main__':
    audio_gui = tool_gui(window)
    window.title('Audio to text')
    window.geometry("600x400+10+10")
    window.mainloop()
