# import the required libraries for the app
# make sure you ran the install script

import os                                                # using for managing the "frames" directory
import sys                                               # used for getting the actual path of the pythom script
from shutil import rmtree                                # used for removing directories
from subprocess import CalledProcessError, check_output  # running and checking the status of ffmpeg (must be installed)
from tkinter import filedialog, PhotoImage               # pop-up box with a list of files for the user to choose, and icon for the window

import customtkinter as CTk                              # the main interface for the app
from webbrowser import open                              # open links
import cv2                                               # image processing and webcam capture
import numpy as np                                       # converting images to np array to work with cv2
import pyclip                                            # copying text to user's clipboard
import pytesseract                                       # using the tesseract program, make sure it's installed on your system
import pyttsx3                                           # text-to-speech
from PIL import Image                                    # placeholder images, opening images and converting images to array to display them in CTk

from CTkMessagebox.CTkMessagebox import *                # pop-up message boxes to display to the user in case of forgetting to add an image or when an error occurs
from CTkToolTip.CTkToolTip import *                      # pop-up boxes when you hover on a widget

reader = pyttsx3.init()  # initalize the text-to-speech engine
CTk.set_default_color_theme(sys.path[0] + "/res/Theme.json")  # load the theme found in the "res" folder. make sure the folder is on the same path as the script.

# for windows users: make sure tesseract.exe is installed in C:\Program Files\Tesseract-OCR
if sys.platform.startswith("win"):
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


class App(CTk.CTk):
    def __init__(self):
        super().__init__()

        # window properties

        self.title("Pic2Text")
        self.grid_columnconfigure((0, 1, 2), weight=1)
        self.grid_rowconfigure((0, 1), weight=1)
        self.minsize(1070, 835)
        self.iconphoto(True, PhotoImage(file=sys.path[0] + "/res/Pic2Image.png"))

        # variables

        self.picked_image = []
        self.webcam_image = []
        self.video_image = []
        self.image_target = []
        self.current_tooltips = []
        self.dpi = 70
        self.psm = 1
        self.tool_tips = 1
        self.brightness = 0
        self.contrast = 1
        self.blur_amount = 0
        self.about_window = None

        # tabview

        self.tabview_frame = CTk.CTkFrame(self)
        self.tabview_frame.grid(padx=5, pady=5, row=0, column=0, sticky="nsew")

        self.tabview = CTk.CTkTabview(self.tabview_frame, corner_radius=10, height=400)
        self.open_file_tab = self.tabview.add("User Image")
        self.webcam_capture_tab = self.tabview.add("Webcam Capture")
        self.video_frame_extractor_tab = self.tabview.add("Video Frame Extractor")
        self.tabview.pack(padx=5, pady=5, expand=True, fill="both")

        # open_file

        self.open_file_frame = CTk.CTkFrame(self.open_file_tab, corner_radius=10)
        self.open_file_frame.pack(expand=True, fill="both")

        self.open_file_frame.rowconfigure(1, weight=1)
        self.open_file_frame.columnconfigure(0, weight=1)

        self.open_file_file_pick = CTk.CTkButton(
            self.open_file_frame,
            text="Choose an image",
            command=self.read_user_image,
        )
        self.open_file_file_pick.grid(padx=5, pady=5, sticky="nwe")

        self.open_file_image = CTk.CTkImage(light_image=Image.new("RGBA", (1, 1), (0, 0, 0, 50)), size=(419, 236))

        self.open_file_image_preview = CTk.CTkLabel(
            self.open_file_frame, image=self.open_file_image, text=""
        )
        self.open_file_image_preview.grid(padx=5, pady=5, sticky="nsew")

        # webcam_capture

        self.webcam_capture_frame = CTk.CTkFrame(self.webcam_capture_tab, corner_radius=10)
        self.webcam_capture_frame.pack(expand=True, fill="both")

        self.webcam_capture_frame.rowconfigure(1, weight=1)
        self.webcam_capture_frame.columnconfigure(0, weight=1)

        self.webcam_capture_take_photo = CTk.CTkButton(
            self.webcam_capture_frame,
            text="Take photo",
            command=self.take_picture,
        )
        self.webcam_capture_take_photo.grid(padx=5, pady=5, sticky="nwe")

        self.webcam_capture_image = CTk.CTkImage(light_image=Image.new("RGBA", (1, 1), (0, 0, 0, 50)), size=(419, 236))
        self.webcam_capture_image_preview = CTk.CTkLabel(
            self.webcam_capture_frame, image=self.webcam_capture_image, text=""
        )
        self.webcam_capture_image_preview.grid(padx=5, pady=5, sticky="nsew")

        # video_frame_extractor

        self.video_frame_extractor_frame = CTk.CTkFrame(self.video_frame_extractor_tab, corner_radius=10)
        self.video_frame_extractor_frame.pack(expand=True, fill="both")

        self.video_frame_extractor_frame.rowconfigure(2, weight=1)
        self.video_frame_extractor_frame.columnconfigure(0, weight=1)

        self.video_frame_extractor_image = CTk.CTkImage(light_image=Image.new("RGBA", (1, 1), (0, 0, 0, 50)), size=(419, 236))

        self.video_frame_extractor_open_video = CTk.CTkButton(
            self.video_frame_extractor_frame,
            text="Choose a video",
            command=self.extract_frames,
        )
        self.video_frame_extractor_open_video.grid(padx=5, pady=5, sticky="nwe")

        self.video_frame_extractor_slider = CTk.CTkSlider(
            self.video_frame_extractor_frame,
            state="disabled",
            command=self.read_frame,
        )
        self.video_frame_extractor_slider.grid(padx=5, pady=5, sticky="nwe")

        self.video_frame_extractor_image_preview = CTk.CTkLabel(
            self.video_frame_extractor_frame,
            image=self.video_frame_extractor_image,
            text="",
        )
        self.video_frame_extractor_image_preview.grid(padx=5, pady=5, sticky="nsew")

        # recognized_text

        self.recognized_text_frame = CTk.CTkFrame(self)
        self.recognized_text_frame.grid(
            row=0, rowspan=2, column=1, padx=5, pady=5, sticky="nsew"
        )

        self.recognized_text_title = CTk.CTkLabel(
            self.recognized_text_frame,
            text="Recognized text",
            font=CTk.CTkFont(size=20, weight="bold"),
        )
        self.recognized_text_title.pack(padx=5, pady=5)

        self.recognized_text_textbox = CTk.CTkTextbox(
            self.recognized_text_frame, state="disabled", corner_radius=10
        )
        self.recognized_text_textbox.pack(padx=5, pady=5, fill="both", expand=True)

        self.recognized_text_copy_text = CTk.CTkButton(
            self.recognized_text_frame,
            text="Copy text",
            command=self.copy_recognized_text,
        )
        self.recognized_text_copy_text.pack(padx=5, pady=5, fill="x")

        # bounding_boxes

        self.bounding_boxes_frame = CTk.CTkFrame(self)
        self.bounding_boxes_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        self.bounding_boxes_title = CTk.CTkLabel(
            self.bounding_boxes_frame,
            text="Bounding box estimates",
            font=CTk.CTkFont(size=20, weight="bold"),
        )
        self.bounding_boxes_title.pack(padx=5, pady=5)

        self.bounding_boxes_image = CTk.CTkImage(light_image=Image.new("RGBA", (1, 1), (0, 0, 0, 50)), size=(419, 236))

        self.bounding_boxes_image_preview = CTk.CTkLabel(
            self.bounding_boxes_frame, image=self.bounding_boxes_image, text=""
        )
        self.bounding_boxes_image_preview.pack(padx=5, pady=5, expand=True, fill="both")

        # actions

        self.actions_frame = CTk.CTkFrame(self)
        self.actions_frame.grid(
            row=2, column=0, columnspan=3, padx=5, pady=5, sticky="nsew"
        )

        self.actions_run_ocr_button = CTk.CTkButton(
            self.actions_frame,
            text="Start detecting text",
            width=200,
            command=self.run_pytesseract,
        )
        self.actions_run_ocr_button.pack(padx=5, pady=5)

        self.actions_read_aloud_text = CTk.CTkButton(
            self.actions_frame,
            text="Read the recognized text aloud",
            width=200,
            command=self.read_aloud_text,
        )
        self.actions_read_aloud_text.pack(padx=5, pady=5)

        # options

        self.options_frame = CTk.CTkFrame(self)
        self.options_frame.grid(
            row=0, column=2, rowspan=2, padx=5, pady=5, sticky="nsew"
        )

        self.options_title = CTk.CTkLabel(
            self.options_frame,
            text="Options",
            font=CTk.CTkFont(size=20, weight="bold"),
        )
        self.options_title.pack(padx=5, pady=5)

        self.dark_mode_option = CTk.CTkCheckBox(
            self.options_frame,
            text="Use dark mode",
            checkbox_width=50,
            command=self.change_dark_mode_option,
        )
        self.dark_mode_option.toggle()
        self.dark_mode_option.pack(padx=5, pady=5)

        self.make_bell_option = CTk.CTkCheckBox(
            self.options_frame,
            text='Enable window "Ding"',
            checkbox_width=50,
        )
        self.make_bell_option.toggle()
        self.make_bell_option.pack(padx=5, pady=5)

        self.tool_tips_option = CTk.CTkCheckBox(
            self.options_frame,
            text="Show pop-up help",
            checkbox_width=50,
            command=self.change_tooltips_option,
        )
        self.tool_tips_option.toggle()
        self.tool_tips_option.pack(padx=5, pady=5)

        self.separator = CTk.CTkFrame(self.options_frame, height=10)
        self.separator.pack(padx=10, pady=5, fill="x")

        self.options_image = CTk.CTkImage(
            light_image=Image.new("RGBA", (1, 1), (0, 0, 0, 50)),
            size=(240, 150),
        )

        self.options_image_preview = CTk.CTkLabel(
            self.options_frame, image=self.options_image, text=""
        )
        self.options_image_preview.pack(padx=5, pady=5)

        self.brightness_option_label = CTk.CTkLabel(
            self.options_frame, text="Image brightness"
        )
        self.brightness_option_label.pack(padx=1, pady=2)

        self.brightness_option = CTk.CTkSlider(
            self.options_frame,
            from_=-64,
            to=64,
            width=256,
            command=self.change_brightness,
        )
        self.brightness_option.pack(padx=5, pady=5)

        self.brightness_option_reset = CTk.CTkButton(
            self.options_frame,
            text="Reset brightness",
            command=self.reset_brightness,
        )
        self.brightness_option_reset.pack(padx=5, pady=5)

        self.contrast_option_label = CTk.CTkLabel(
            self.options_frame, text="Image contrast"
        )
        self.contrast_option_label.pack(padx=1, pady=2)

        self.contrast_option = CTk.CTkSlider(
            self.options_frame,
            from_=0.5,
            to=2,
            width=256,
            command=self.change_contrast,
        )
        self.contrast_option.set(1)
        self.contrast_option.pack(padx=5, pady=5)

        self.contrast_option_reset = CTk.CTkButton(
            self.options_frame,
            text="Reset contrast",
            command=self.reset_contrast,
        )
        self.contrast_option_reset.pack(padx=5, pady=5)

        self.blur_amount_option_label = CTk.CTkLabel(
            self.options_frame, text="Blur amount"
        )
        self.blur_amount_option_label.pack(padx=1, pady=2)

        self.blur_amount_option = CTk.CTkSlider(
            self.options_frame,
            from_=0,
            to=10,
            width=256,
            command=self.change_blur
        )
        self.blur_amount_option.set(0)
        self.blur_amount_option.pack(padx=5, pady=5)

        self.separator = CTk.CTkFrame(self.options_frame, height=10)
        self.separator.pack(padx=10, pady=5, fill="x")

        self.dpi_option = CTk.CTkButton(
            self.options_frame, text="DPI: 70", command=self.change_dpi_option
        )
        self.dpi_option.pack(padx=1, pady=5)

        self.psm_option_label = CTk.CTkLabel(
            self.options_frame, text="Page segmentation mode"
        )
        self.psm_option_label.pack()

        self.psm_option = CTk.CTkOptionMenu(
            self.options_frame,
            width=270,
            dynamic_resizing=False,
            values=[
                "Fully automatic page segmentation. (Default)",
                "Assume a single column of text of variable sizes.",
                "Assume a single uniform block of vertically aligned text.",
                "Assume a single uniform block of text.",
                "Treat the image as a single text line.",
                "Sparse text. Find as much text as possible in no particular order.",
            ],
            command=self.change_psm_option,
        )
        self.psm_option.pack(padx=1, pady=5)

        self.noise_reduce_option = CTk.CTkCheckBox(
            self.options_frame,
            text="Vigorously remove noise",
            checkbox_width=50,
        )
        self.noise_reduce_option.pack(padx=10, pady=5)

        # about

        self.about_button = CTk.CTkButton(
            self.actions_frame,
            fg_color="transparent",
            border_width=0,
            text="About",
            width=0,
            command=self.show_about
        )
        self.about_button.place(relx=1, rely=1, x=-68, y=-32)

        # tooltips

        self.defined_tooltips = [
            [self.open_file_file_pick, "Choose an image from the file picker."],
            [self.open_file_image_preview, "This is a preview of the image you have picked."],
            [self.webcam_capture_take_photo, "Take a picture from your webcam."],
            [self.webcam_capture_image_preview, "This is a preview of the image you have taken from your webcam."],
            [self.video_frame_extractor_open_video, "Open a supported video file."],
            [self.video_frame_extractor_slider, "This is the video slider. Drag it to change the current frame of the video."],
            [self.bounding_boxes_image_preview, "This image shows blue boxes, where the app detected some text."],
            [self.video_frame_extractor_image_preview, "This is the current frame of the video, according to the position of the video slider."],
            [self.recognized_text_textbox, "This is the recognized text from the source. You can select the text and copy it, or read it aloud."],
            [self.recognized_text_copy_text, "Copy the recognized text to your clipboard."],
            [self.actions_run_ocr_button, "Start reading the text from the current source."],
            [self.actions_read_aloud_text, "Clicking this button will make the computer speak the recognized text to you."],
            [self.dark_mode_option, "Changes the current appearance of the app. On: Light mode, Off: Dark mode."],
            [self.options_image_preview, "This is a preview of the image, with the applied brightness and contrast controls."],
            [self.brightness_option, "Drag this slider to change the brightness of the image."],
            [self.brightness_option_reset, "Resets the brightness slider to the default value."],
            [self.make_bell_option, '"Ding" when a message is shown or when a task is complete.'],
            [self.tool_tips_option, "When you hover your pointer on any widget, show information."],
            [self.contrast_option, "Drag this slider to change the contrast of the image."],
            [self.contrast_option_reset, "Resets the contrast slider to the default value."],
            [self.dpi_option, "Optional. Changes DPI of recognized image."],
            [self.psm_option, "Change this option when the text in the image is aligned differently."],
            [self.noise_reduce_option, "Optional. Try enabling this option when there are reading problems."],
            [self.blur_amount_option, "Drag this slider to change the softness of the image."],
            [self.about_button, "Show information about this app."]
        ]

        for defined_tooltip in self.defined_tooltips:
            self.tooltip = CTkToolTip(
                defined_tooltip[0],
                message=defined_tooltip[1],
                bg_color=("gray75", "gray25"),
                justify="left",
                wraplength=150,
                delay=0,
            )
            self.current_tooltips.append(self.tooltip)

    def copy_recognized_text(self):
        try:
            pyclip.copy(self.recognized_text_textbox.get("0.0", "end"))
            if self.make_bell_option.get():
                self.bell()
            CTkMessagebox(
                self,
                title="Message",
                message="The text has been copied to your clipboard.",
                icon="check",
                header=True
            )
        except Exception as e:
            if self.make_bell_option.get():
                self.bell()
            CTkMessagebox(
                self,
                title="Message",
                message=f"There was an error copying text.\n\n{e}",
                icon="cancel",
                height=350,
                header=True,
            )

    def change_tooltips_option(self):
        if self.tool_tips_option.get():
            for i in iter(self.current_tooltips):
                i.show()
        else:
            for i in iter(self.current_tooltips):
                i.hide()

    def change_dark_mode_option(self):
        if self.dark_mode_option.get():
            CTk.set_appearance_mode("dark")
        else:
            CTk.set_appearance_mode("light")

    def change_dpi_option(self):
        self.dpi_input_dialog = CTk.CTkInputDialog(
            text="Change image DPI ( Default: 70, Range: 70 - 2400 )",
            title="Change image DPI",
        )
        try:
            self.dpi = int(self.dpi_input_dialog.get_input())
            if self.dpi > 2400:
                self.dpi = 2400
            elif self.dpi < 70:
                self.dpi = 70
            self.dpi_option.configure(text=f"DPI: {self.dpi}")
        except Exception:
            if self.make_bell_option.get():
                self.bell()
            CTkMessagebox(
                self,
                title="Message",
                message="Invalid value.",
                icon="warning",
                header=True,
            )

    def change_psm_option(self, choice):
        if choice == "Fully automatic page segmentation. (Default)":
            self.psm = 3
        elif choice == "Assume a single column of text of variable sizes.":
            self.psm = 4
        elif choice == "Assume a single uniform block of vertically aligned text.":
            self.psm = 5
        elif choice == "Assume a single uniform block of text.":
            self.psm = 6
        elif choice == "Treat the image as a single text line.":
            self.psm = 7
        elif choice == "Sparse text. Find as much text as possible in no particular order.":
            self.psm = 11

    def read_user_image(self):
        self.user_image = filedialog.askopenfilename(  # ask the user to open an image
            title="Choose an image",
            filetypes=(
                ("", "*.png"),
                ("", "*.jpg"),
                ("", "*.jpeg"),
                ("", "*.webm"),
                ("", "*.PNG"),
                ("", "*.JPG"),
                ("", "*.JPEG"),
                ("", "*.WEBM"),
            ),
        )
        if not len(self.user_image) == 0:  # check if the user didn't pick an image, or if the image is not empty
            try:
                self.picked_image = Image.open(self.user_image)
                self.open_file_image.configure(light_image=self.picked_image)
                self.process_image(self.picked_image)
                self.options_image.configure(light_image=Image.fromarray(self.image_target))
            except Exception as e:
                if self.make_bell_option.get():
                    self.bell()
                CTkMessagebox(
                    self,
                    title="Message",
                    message=f"Failed to open image.\n\n{e}",
                    icon="cancel",
                    height=350,
                    header=True
                )

    def change_brightness(self, value):
        self.brightness = value
        self.check_image()

    def change_contrast(self, value):
        self.contrast = value
        self.check_image()

    def change_blur(self, value):
        self.blur_amount = int(value)
        self.check_image()

    def reset_brightness(self):
        self.brightness_option.set(0)
        self.change_brightness(0)

    def reset_contrast(self):
        self.contrast_option.set(1)
        self.change_contrast(1)

    def take_picture(self):
        self.cam = cv2.VideoCapture(0)
        self.result, self.image = self.cam.read()
        if self.result:
            self.webcam_image = Image.fromarray(
                cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
            )
            self.webcam_capture_image.configure(light_image=self.webcam_image)
            self.process_image(self.webcam_image)
            self.options_image.configure(light_image=Image.fromarray(self.image_target))
            self.cam = cv2.VideoCapture(0)
        else:
            self.webcam_capture_image.configure(light_image=Image.new("RGBA", (1, 1), (0, 0, 0, 50)), size=(419, 236))
            if self.make_bell_option.get():
                self.bell()
            CTkMessagebox(
                self,
                title="Message",
                message="Failed to capture image. Please try again.",
                icon="cancel",
                header=True,
            )

    def extract_frames(self):
        self.video = filedialog.askopenfilename(title="Choose a video")

        if not len(self.video) == 0:  # Check if video is empty before running
            if os.path.isdir("frames"):  # Remake directory if it exists
                rmtree("frames")
                os.mkdir("frames")
            else:
                os.mkdir("frames")

            # Split the video into frames (ffmpeg required)
            try:
                check_output(
                    "ffmpeg -i "
                    + '"'
                    + self.video
                    + '"'
                    + " frames/thumb%04d.png -hide_banner",
                    shell=True,
                )
                # Use the frames directory
                self.directories = sorted(os.listdir("frames"))
                self.frames = []
                for i in range(len(self.directories)):
                    self.frames.append(str(i))
                if len(self.directories) == 1:
                    self.video_frame_extractor_slider.configure(state="disabled")
                else:
                    self.video_frame_extractor_slider.configure(
                        state="normal", to=len(self.directories) - 1
                    )
                if self.make_bell_option.get():
                    self.bell()
                self.read_frame(0)
            except CalledProcessError:
                if self.make_bell_option.get():
                    self.bell()
                CTkMessagebox(
                    self,
                    title="Message",
                    message=f"Please choose a supported video file.",
                    icon="cancel",
                    header=True,
                )

    def read_frame(self, value):
        self.video_image = Image.open("frames/" + self.directories[int(value)])
        self.video_frame_extractor_image.configure(light_image=self.video_image)
        self.process_image(self.video_image)
        self.options_image.configure(light_image=Image.fromarray(self.image_target))

    def read_aloud_text(self):
        print("speaking...")
        reader.say(self.recognized_text_textbox.get("0.0", "end"))
        reader.runAndWait()
        if self.make_bell_option.get():
            self.bell()
        print("done.")

    def process_image(self, image):
        if self.blur_amount > 1:
            self.image_target = cv2.blur(cv2.convertScaleAbs(  # apply brightness and contrast controls to image
                np.asarray(image),  # convert the image to numpy array for the function to work
                alpha=self.contrast,
                beta=self.brightness,
            ), (self.blur_amount, self.blur_amount))
        else:
            self.image_target = cv2.convertScaleAbs(  # apply brightness and contrast controls to image
                np.asarray(image),  # convert the image to numpy array for the function to work
                alpha=self.contrast,
                beta=self.brightness,
            )

    def check_image(self):
        if self.tabview.get() == "User Image":  # if the image source is "User Image"
            if not self.picked_image == []:  # check that the image is not empty
                self.process_image(self.picked_image)
                self.options_image.configure(light_image=Image.fromarray(self.image_target))  # show preview of the current image
                return True  # confirm the image is checked
            else:
                if self.make_bell_option.get():
                    self.bell()
                CTkMessagebox(
                    self,
                    title="Message",
                    message="There is no image, please add an image to the chosen source.",
                    icon="warning",
                    header=True,
                )
                return False  # means there is no image
        elif self.tabview.get() == "Webcam Capture":  # if the image source is "Webcam Capture"
            if not self.webcam_image == []:  # check that the image is not empty
                self.process_image(self.webcam_image)
                self.options_image.configure(light_image=Image.fromarray(self.image_target))  # show preview of the current image
                return True  # confirm the image is checked
            else:
                if self.make_bell_option.get():
                    self.bell()
                CTkMessagebox(
                    self,
                    title="Message",
                    message="There is no image, please add an image to the chosen source.",
                    icon="warning",
                    header=True,
                )
                return False  # means there is no image
        elif self.tabview.get() == "Video Frame Extractor":  # if the image source is "Video Frame Extractor"
            if not self.video_image == []:  # check that the image is not empty
                self.process_image(self.video_image)
                self.options_image.configure(light_image=Image.fromarray(self.image_target))  # show preview of the current image
                return True  # confirm the image is checked
            else:
                if self.make_bell_option.get():
                    self.bell()
                CTkMessagebox(
                    self,
                    title="Message",
                    message="There is no image, please add an image to the chosen source.",
                    icon="warning",
                    header=True,
                )
                return False  # means there is no image

    def run_pytesseract(self):
        if self.check_image():
            try:
                # Convert image to string
                self.image_to_string = pytesseract.image_to_string(
                    self.image_target,
                    config=f'-c page_separator="" --dpi {self.dpi} --psm {self.psm} -c textord_heavy_nr={self.noise_reduce_option.get()}',
                )
                self.recognized_text_textbox.configure(state="normal")
                self.recognized_text_textbox.delete("0.0", "end")
                self.recognized_text_textbox.insert("0.0", self.image_to_string)
                self.recognized_text_textbox.configure(state="disabled")
                print(self.image_to_string)

                # Draw bounding boxes and data
                self.results = pytesseract.image_to_data(
                    self.image_target,
                    config=f"--dpi {self.dpi} --psm {self.psm} -c textord_heavy_nr={self.noise_reduce_option.get()}",
                    output_type=pytesseract.Output.DICT,
                )
                self.image_target = cv2.cvtColor(
                    np.asarray(self.image_target), cv2.COLOR_RGB2BGR
                )
                for i in range(len(self.results["text"])):
                    # extract the bounding box coordinates of the text region from the current result
                    tmp_tl_x = self.results["left"][i]
                    tmp_tl_y = self.results["top"][i]
                    tmp_br_x = tmp_tl_x + self.results["width"][i]
                    tmp_br_y = tmp_tl_y + self.results["height"][i]
                    tmp_level = self.results["level"][i]

                    if tmp_level == 5:
                        self.image_target = cv2.rectangle(
                            self.image_target,
                            (tmp_tl_x, tmp_tl_y),
                            (tmp_br_x, tmp_br_y),
                            255,
                            1,
                        )
                self.image_target = cv2.cvtColor(self.image_target, cv2.COLOR_BGR2RGB)
                self.bounding_boxes_image.configure(
                    light_image=Image.fromarray(self.image_target)
                )
                if self.make_bell_option.get():
                    self.bell()
            except Exception as e:
                if self.make_bell_option.get():
                    self.bell()
                CTkMessagebox(
                    self,
                    title="Message",
                    message=f"There was an error while processing text.\n\n{e}",
                    icon="cancel",
                    height=350,
                    header=True,
                )
    def show_about(self):
        if self.about_window is None or not self.about_window.winfo_exists():
            self.about_window = CTk.CTkToplevel(self)  # create window if its None or destroyed
            self.about_window.title("About Pic2Text")
            self.about_window.resizable(False, False)

            self.about_logo_image = CTk.CTkImage(
                light_image=Image.open(sys.path[0] + "/res/Pic2Image.png"),
                size=(322, 293)
            )

            self.about_logo = CTk.CTkButton(
                self.about_window,
                text="This logo was designed using Inkscape",
                compound="top",
                border_width=0,
                image=self.about_logo_image,
                fg_color="transparent",
                hover=False,
                font=CTk.CTkFont(underline=True),
                command=lambda: open("https://inkscape.org/"),
            ).pack(side="left", padx=5, pady=5)

            self.about_app_description = CTk.CTkLabel(
                self.about_window,
                text="Pic2Text is an app that recognizes text from image, using Tesseract OCR with a user-friendly interface.",
                wraplength=400,
            ).pack(pady=5)

            self.about_tabview = CTk.CTkTabview(self.about_window)
            self.libraries_tab = self.about_tabview.add("Libraries & External Programs")
            self.project_links_tab = self.about_tabview.add("Project Links")
            self.contact_tab = self.about_tabview.add("Contact Me")
            self.about_tabview.pack(padx=5, pady=5)

            self.about_app_utilize = CTk.CTkLabel(
                self.libraries_tab,
                text="This app utilizes:",
                font=CTk.CTkFont(size=19),
            ).pack()

            self.libraries_links = [
                ["CustomTkinter", "https://github.com/TomSchimansky/CustomTkinter"],
                ["CTkMessagebox", "https://github.com/Akascape/CTkMessagebox"],
                ["CTkToolTip", "https://github.com/Akascape/CTkToolTip"],
                ["tkinter", "https://docs.python.org/3/library/tkinter.html"],
                ["Tesseract OCR", "https://github.com/tesseract-ocr/tesseract"],
                ["pytesseract", "https://pypi.org/project/pytesseract/"],
                ["pyttsx3", "https://pypi.org/project/pyttsx3/"],
                ["subprocess", "https://docs.python.org/3/library/subprocess.html"],
                ["ffmpeg", "https://ffmpeg.org/"],
                ["opencv-python", "https://pypi.org/project/opencv-python/"],
                ["pyclip", "https://pypi.org/project/pyclip/"],
                ["Pillow", "https://pypi.org/project/Pillow/"],
                ["numpy", "https://pypi.org/project/numpy/"]
            ]

            self.project_links = [
                ["User Manual", "https://raw.githubusercontent.com/LoKiToon/Pic2Text/master/Pic2Text_User_Manual.pdf"],
                ["Demo Video", "https://youtu.be/ZR5BAkcbMqY"],
                ["Github Launch", "https://github.com/LoKiToon/Pic2Text"],
                ["LinkedIn Launch", "https://www.linkedin.com/pulse/recognize-text-from-image-user-friendly-interface-pic2text-taibeh"],
                ["App Development Toolkit", "https://docs.google.com/spreadsheets/d/1huna7g1E7eWEHNenM4X6gNFcnYXJcmq-/edit?usp=sharing&ouid=104577051238204190186&rtpof=true&sd=true"],
            ]

            self.contact_links = [
                ["My Github Profile", "https://github.com/LoKiToon"],
                ["Email: NisTroAti@proton.me", "mailto:NisTroAti@proton.me"]
            ]

            def create_link(link, tab):
                self.about_link = CTk.CTkButton(
                    tab,
                    text=link[0],
                    height=0,
                    border_width=0,
                    fg_color="transparent",
                    hover=False,
                    font=CTk.CTkFont(underline=True),
                    command=lambda: open(link[1]),
                    border_spacing=0
                ).pack()

            for link in self.libraries_links:
                create_link(link, self.libraries_tab)

            for link in self.project_links:
                create_link(link, self.project_links_tab)

            for link in self.contact_links:
                create_link(link, self.contact_tab)
        else:
            self.about_window.focus()  # if window exists focus it


if __name__ == "__main__":
    app = App()
    app.mainloop()

# when the app is exited by the user, remove the frames folder if it exists, as it will be unused

if os.path.isdir("frames"):
    rmtree("frames")