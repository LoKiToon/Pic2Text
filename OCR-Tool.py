# import the required libraries for the app
# make sure you ran the install script

import os
import sys
from shutil import rmtree
from subprocess import CalledProcessError, check_output
from tkinter import filedialog

import customtkinter as CTk
import cv2
import numpy as np
import pyperclip
import pytesseract
import pyttsx3
from PIL import Image

from CTkMessagebox.CTkMessagebox import *
from CTkToolTip.CTkToolTip import *

reader = pyttsx3.init()
CTk.set_default_color_theme(sys.path[0]+"/Theme.json")

if sys.platform.startswith("win"):  # make sure tesseract.exe is installed in C:\Program Files\Tesseract-OCR
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


class App(CTk.CTk):
    def __init__(self):
        super().__init__()

        # window properties

        self.title("The Optical Character Recognition Tool")
        self.grid_columnconfigure((0, 1, 2), weight=1)
        self.grid_rowconfigure((0, 1), weight=1)
        self.minsize(1070, 835)

        # variables

        self.pickedImage = []
        self.webcamImage = []
        self.videoImage = []
        self.imageTarget = []
        self.currentTooltips = []
        self.dpi = 70
        self.psm = 1
        self.toolTips = 1
        self.brightness = 0
        self.contrast = 1
        self.blurAmount = 0

        # tabview

        self.tabview_frame = CTk.CTkFrame(self)
        self.tabview_frame.grid(padx=5, pady=5, row=0, column=0, sticky="nsew")

        self.tabview = CTk.CTkTabview(self.tabview_frame, corner_radius=10, height=400)
        self.openFileTab = self.tabview.add("User Image")
        self.webcamCaptureTab = self.tabview.add("Webcam Capture")
        self.videoFrameExtractorTab = self.tabview.add("Video Frame Extractor")
        self.tabview.pack(padx=5, pady=5, expand=True, fill="both")

        # openFile

        self.openFile_frame = CTk.CTkFrame(self.openFileTab, corner_radius=10)
        self.openFile_frame.pack(expand=True, fill="both")

        self.openFile_frame.rowconfigure(1, weight=1)
        self.openFile_frame.columnconfigure(0, weight=1)

        self.openFile_filePick = CTk.CTkButton(
            self.openFile_frame,
            text="Choose an image",
            command=self.readUserImage,
        )
        self.openFile_filePick.grid(padx=5, pady=5, sticky="nwe")

        self.openFile_image = CTk.CTkImage(light_image=Image.new("RGBA", (1, 1), (0, 0, 0, 50)), size=(419, 236))

        self.openFile_imagePreview = CTk.CTkLabel(
            self.openFile_frame, image=self.openFile_image, text=""
        )
        self.openFile_imagePreview.grid(padx=5, pady=5, sticky="nsew")

        # webcamCapture

        self.webcamCapture_frame = CTk.CTkFrame(self.webcamCaptureTab, corner_radius=10)
        self.webcamCapture_frame.pack(expand=True, fill="both")

        self.webcamCapture_frame.rowconfigure(1, weight=1)
        self.webcamCapture_frame.columnconfigure(0, weight=1)

        self.webcamCapture_takePhoto = CTk.CTkButton(
            self.webcamCapture_frame,
            text="Take photo",
            command=self.takePicture,
        )
        self.webcamCapture_takePhoto.grid(padx=5, pady=5, sticky="nwe")

        self.webcamCapture_image = CTk.CTkImage(light_image=Image.new("RGBA", (1, 1), (0, 0, 0, 50)), size=(419, 236))
        self.webcamCapture_imagePreview = CTk.CTkLabel(
            self.webcamCapture_frame, image=self.webcamCapture_image, text=""
        )
        self.webcamCapture_imagePreview.grid(padx=5, pady=5, sticky="nsew")

        # videoFrameExtractor

        self.videoFrameExtractor_frame = CTk.CTkFrame(self.videoFrameExtractorTab, corner_radius=10)
        self.videoFrameExtractor_frame.pack(expand=True, fill="both")

        self.videoFrameExtractor_frame.rowconfigure(2, weight=1)
        self.videoFrameExtractor_frame.columnconfigure(0, weight=1)

        self.videoFrameExtractor_image = CTk.CTkImage(light_image=Image.new("RGBA", (1, 1), (0, 0, 0, 50)), size=(419, 236))

        self.videoFrameExtractor_openVideo = CTk.CTkButton(
            self.videoFrameExtractor_frame,
            text="Choose a video",
            command=self.extractFrames,
        )
        self.videoFrameExtractor_openVideo.grid(padx=5, pady=5, sticky="nwe")
        
        self.videoFrameExtractor_slider = CTk.CTkSlider(
            self.videoFrameExtractor_frame,
            state="disabled",
            command=self.readFrame,
        )
        self.videoFrameExtractor_slider.grid(padx=5, pady=5, sticky="nwe")

        self.videoFrameExtractor_imagePreview = CTk.CTkLabel(
            self.videoFrameExtractor_frame,
            image=self.videoFrameExtractor_image,
            text="",
        )
        self.videoFrameExtractor_imagePreview.grid(padx=5, pady=5, sticky="nsew")

        # recognizedText

        self.recognizedText_frame = CTk.CTkFrame(self)
        self.recognizedText_frame.grid(
            row=0, rowspan=2, column=1, padx=5, pady=5, sticky="nsew"
        )

        self.recognizedText_title = CTk.CTkLabel(
            self.recognizedText_frame,
            text="Recognized text",
            font=CTk.CTkFont(size=20, weight="bold"),
        )
        self.recognizedText_title.pack(padx=5, pady=5)

        self.recognizedText_textBox = CTk.CTkTextbox(
            self.recognizedText_frame, state="disabled", corner_radius=10
        )
        self.recognizedText_textBox.pack(padx=5, pady=5, fill="both", expand=True)

        self.recognizedText_copyText = CTk.CTkButton(
            self.recognizedText_frame,
            text="Copy text",
            command=self.copyRecognizedText,
        )
        self.recognizedText_copyText.pack(padx=5, pady=5, fill="x")

        # boundingBoxes

        self.boundingBoxes_frame = CTk.CTkFrame(self)
        self.boundingBoxes_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        self.boundingBoxes_title = CTk.CTkLabel(
            self.boundingBoxes_frame,
            text="Bounding box estimates",
            font=CTk.CTkFont(size=20, weight="bold"),
        )
        self.boundingBoxes_title.pack(padx=5, pady=5)

        self.boundingBoxes_image = CTk.CTkImage(light_image=Image.new("RGBA", (1, 1), (0, 0, 0, 50)), size=(419, 236))

        self.boundingBoxes_imagePreview = CTk.CTkLabel(
            self.boundingBoxes_frame, image=self.boundingBoxes_image, text=""
        )
        self.boundingBoxes_imagePreview.pack(padx=5, pady=5, expand=True, fill="both")

        # actions

        self.actions_frame = CTk.CTkFrame(self)
        self.actions_frame.grid(
            row=2, column=0, columnspan=3, padx=5, pady=5, sticky="nsew"
        )

        self.actions_runOCRbutton = CTk.CTkButton(
            self.actions_frame,
            text="Start detecting text",
            width=200,
            command=self.runPytesseract,
        )
        self.actions_runOCRbutton.pack(padx=5, pady=5)

        self.actions_readAloudText = CTk.CTkButton(
            self.actions_frame,
            text="Read the recognized text aloud",
            width=200,
            command=self.readAloudText,
        )
        self.actions_readAloudText.pack(padx=5, pady=5)

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

        self.darkMode_option = CTk.CTkCheckBox(
            self.options_frame,
            text="Use dark mode",
            checkbox_width=50,
            command=self.changedarkModeOption,
        )
        self.darkMode_option.toggle()
        self.darkMode_option.pack(padx=5, pady=5)

        self.makeBell_option = CTk.CTkCheckBox(
            self.options_frame,
            text='Enable window "Ding"',
            checkbox_width=50,
        )
        self.makeBell_option.toggle()
        self.makeBell_option.pack(padx=5, pady=5)

        self.toolTips_option = CTk.CTkCheckBox(
            self.options_frame,
            text="Show pop-up help",
            checkbox_width=50,
            command=self.changetoolTipsOption,
        )
        self.toolTips_option.toggle()
        self.toolTips_option.pack(padx=5, pady=5)

        self.separator = CTk.CTkFrame(self.options_frame, height=10)
        self.separator.pack(padx=10, pady=5, fill="x")

        self.options_image = CTk.CTkImage(
            light_image=Image.new("RGBA", (1, 1), (0, 0, 0, 50)),
            size=(240, 150),
        )

        self.options_imagePreview = CTk.CTkLabel(
            self.options_frame, image=self.options_image, text=""
        )
        self.options_imagePreview.pack(padx=5, pady=5)

        self.brightness_optionLabel = CTk.CTkLabel(
            self.options_frame, text="Image brightness"
        )
        self.brightness_optionLabel.pack(padx=1, pady=2)

        self.brightness_option = CTk.CTkSlider(
            self.options_frame,
            from_=-64,
            to=64,
            width=256,
            command=self.changeBrightness,
        )
        self.brightness_option.pack(padx=5, pady=5)

        self.brightness_optionReset = CTk.CTkButton(
            self.options_frame,
            text="Reset brightness",
            command=self.resetBrightness,
        )
        self.brightness_optionReset.pack(padx=5, pady=5)

        self.contrast_optionLabel = CTk.CTkLabel(
            self.options_frame, text="Image contrast"
        )
        self.contrast_optionLabel.pack(padx=1, pady=2)

        self.contrast_option = CTk.CTkSlider(
            self.options_frame,
            from_=0.5,
            to=2,
            width=256,
            command=self.changeContrast,
        )
        self.contrast_option.set(1)
        self.contrast_option.pack(padx=5, pady=5)

        self.contrast_optionReset = CTk.CTkButton(
            self.options_frame,
            text="Reset contrast",
            command=self.resetContrast,
        )
        self.contrast_optionReset.pack(padx=5, pady=5)

        self.blurAmount_optionLabel = CTk.CTkLabel(
            self.options_frame, text="Blur amount"
        )
        self.blurAmount_optionLabel.pack(padx=1, pady=2)

        self.blurAmount_option = CTk.CTkSlider(
            self.options_frame,
            from_=0,
            to=10,
            width=256,
            command=self.changeBlur
        )
        self.blurAmount_option.set(0)
        self.blurAmount_option.pack(padx=5, pady=5)

        self.separator = CTk.CTkFrame(self.options_frame, height=10)
        self.separator.pack(padx=10, pady=5, fill="x")

        self.dpi_option = CTk.CTkButton(
            self.options_frame, text="DPI: 70", command=self.changedpiOption
        )
        self.dpi_option.pack(padx=1, pady=5)

        self.psm_optionLabel = CTk.CTkLabel(
            self.options_frame, text="Page segmentation mode"
        )
        self.psm_optionLabel.pack()

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
            command=self.changepsmOption,
        )
        self.psm_option.pack(padx=1, pady=5)

        self.noiseRd_option = CTk.CTkCheckBox(
            self.options_frame,
            text="Vigorously remove noise",
            checkbox_width=50,
        )
        self.noiseRd_option.pack(padx=10, pady=5)

        # tooltips

        self.definedTooltips = [
            [self.openFile_filePick, "Choose an image from the file picker."],
            [self.openFile_imagePreview, "This is a preview of the image you have picked."],
            [self.webcamCapture_takePhoto, "Take a picture from your webcam."],
            [self.webcamCapture_imagePreview, "This is a preview of the image you have taken from your webcam."],
            [self.videoFrameExtractor_openVideo, "Open a supported video file."],
            [self.videoFrameExtractor_slider, "This is the video slider. Drag it to change the current frame of the video."],
            [self.boundingBoxes_imagePreview, "This image shows blue boxes, where the app detected some text."],
            [self.videoFrameExtractor_imagePreview, "This is the current frame of the video, according to the position of the video slider."],
            [self.recognizedText_textBox, "This is the recognized text from the source. You can select the text and copy it, or read it aloud."],
            [self.recognizedText_copyText, "Copy the recognized text to your clipboard."],
            [self.actions_runOCRbutton, "Start reading the text from the current source."],
            [self.actions_readAloudText, "Clicking this button will make the computer speak the recognized text to you."],
            [self.darkMode_option, "Changes the current appearance of the app. On: Light mode, Off: Dark mode."],
            [self.options_imagePreview, "This is a preview of the image, with the applied brightness and contrast controls."],
            [self.brightness_option, "Drag this slider to change the brightness of the image."],
            [self.brightness_optionReset, "Resets the brightness slider to the default value."],
            [self.makeBell_option, '"Ding" when a message is shown or when a task is complete.'],
            [self.toolTips_option, "When you hover your pointer on any widget, show information."],
            [self.contrast_option, "Drag this slider to change the contrast of the image."],
            [self.contrast_optionReset, "Resets the contrast slider to the default value."],
            [self.dpi_option, "Optional. Changes DPI of recognized image."],
            [self.psm_option, "Change this option when the text in the image is aligned differently."],
            [self.noiseRd_option, "Optional. Try enabling this option when there are reading problems."],
            [self.blurAmount_option, "Drag this slider to change the softness of the image."]
        ]

        for i in range(len(self.definedTooltips)):
            self.tooltip = CTkToolTip(
                self.definedTooltips[i][0],
                message=self.definedTooltips[i][1],
                bg_color=("gray75", "gray25"),
                justify="left",
                wraplength=150,
                delay=0,
            )
            self.currentTooltips.append(self.tooltip)
            
    def copyRecognizedText(self):
        try:
            pyperclip.copy(self.recognizedText_textBox.get("0.0", "end"))
            if self.makeBell_option.get():
                self.bell()
            CTkMessagebox(
                self,
                title="Message",
                message="The text has been copied to your clipboard.",
                icon="check",
                header=True
            )
        except Exception as e:
            if self.makeBell_option.get():
                self.bell()
            CTkMessagebox(
                self,
                title="Message",
                message=f"There was an error copying text.\n\n{e}",
                icon="cancel",
                height=350,
                header=True,
            )

    def changetoolTipsOption(self):
        if self.toolTips_option.get():
            for i in iter(self.currentTooltips):
                i.show()
        else:
            for i in iter(self.currentTooltips):
                i.hide()

    def changedarkModeOption(self):
        if self.darkMode_option.get():
            CTk.set_appearance_mode("dark")
        else:
            CTk.set_appearance_mode("light")

    def changedpiOption(self):
        self.dpiInpDialog = CTk.CTkInputDialog(
            text="Change image DPI ( Default: 70, Range: 70 - 2400 )",
            title="Change image DPI",
        )
        try:
            self.dpi = int(self.dpiInpDialog.get_input())
            if self.dpi > 2400:
                self.dpi = 2400
            elif self.dpi < 70:
                self.dpi = 70
            self.dpi_option.configure(text=f"DPI: {self.dpi}")
        except Exception:
            if self.makeBell_option.get():
                self.bell()
            CTkMessagebox(
                self,
                title="Message",
                message="Invalid value.",
                icon="warning",
                header=True,
            )

    def changepsmOption(self, choice):
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

    def readUserImage(self):
        self.userImage = filedialog.askopenfilename(  # ask the user to open an image
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
        if not len(self.userImage) == 0:  # check if the user didn't pick an image, or if the image is not empty
            try:
                self.pickedImage = Image.open(self.userImage)
                self.openFile_image.configure(light_image=self.pickedImage)
                self.processImage(self.pickedImage)
                self.options_image.configure(light_image=Image.fromarray(self.imageTarget))
            except Exception as e:
                if self.makeBell_option.get():
                    self.bell()
                CTkMessagebox(
                    self,
                    title="Message",
                    message=f"Failed to open image.\n\n{e}",
                    icon="cancel",
                    height=350,
                    header=True
                )

    def changeBrightness(self, value):
        self.brightness = value
        self.checkImage()

    def changeContrast(self, value):
        self.contrast = value
        self.checkImage()

    def changeBlur(self, value):
        self.blurAmount = int(value)
        self.checkImage()

    def resetBrightness(self):
        self.brightness_option.set(0)
        self.changeBrightness(0)

    def resetContrast(self):
        self.contrast_option.set(1)
        self.changeContrast(1)

    def takePicture(self):
        self.cam = cv2.VideoCapture(0)
        self.result, self.image = self.cam.read()
        if self.result:
            self.webcamImage = Image.fromarray(
                cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
            )
            self.webcamCapture_image.configure(light_image=self.webcamImage)
            self.processImage(self.webcamImage)
            self.options_image.configure(light_image=Image.fromarray(self.imageTarget))
            self.cam = cv2.VideoCapture(0)
        else:
            self.webcamCapture_image.configure(light_image=Image.new("RGBA", (1, 1), (0, 0, 0, 50)), size=(419, 236))
            if self.makeBell_option.get():
                self.bell()
            CTkMessagebox(
                self,
                title="Message",
                message="Failed to capture image. Please try again.",
                icon="cancel",
                header=True,
            )

    def extractFrames(self):
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
                    self.videoFrameExtractor_slider.configure(state="disabled")
                else:
                    self.videoFrameExtractor_slider.configure(
                        state="normal", to=len(self.directories) - 1
                    )
                if self.makeBell_option.get():
                    self.bell()
                self.readFrame(0)
            except CalledProcessError:
                if self.makeBell_option.get():
                    self.bell()
                CTkMessagebox(
                    self,
                    title="Message",
                    message=f"Please choose a supported video file.",
                    icon="cancel",
                    header=True,
                )

    def readFrame(self, value):
        self.videoImage = Image.open("frames/" + self.directories[int(value)])
        self.videoFrameExtractor_image.configure(light_image=self.videoImage)
        self.processImage(self.videoImage)
        self.options_image.configure(light_image=Image.fromarray(self.imageTarget))

    def readAloudText(self):
        print("speaking...")
        reader.say(self.recognizedText_textBox.get("0.0", "end"))
        reader.runAndWait()
        if self.makeBell_option.get():
            self.bell()
        print("done.")

    def processImage(self, image):
        if self.blurAmount > 1:
            self.imageTarget = cv2.blur(cv2.convertScaleAbs(  # apply brightness and contrast controls to image
                np.asarray(image),  # convert the image to numpy array for the function to work
                alpha=self.contrast,
                beta=self.brightness,
            ), (self.blurAmount, self.blurAmount))
        else:
            self.imageTarget = cv2.convertScaleAbs(  # apply brightness and contrast controls to image
                np.asarray(image),  # convert the image to numpy array for the function to work
                alpha=self.contrast,
                beta=self.brightness,
            )

    def checkImage(self):
        if self.tabview.get() == "User Image":  # if the image source is "User Image"
            if not self.pickedImage == []:  # check that the image is not empty
                self.processImage(self.pickedImage)
                self.options_image.configure(light_image=Image.fromarray(self.imageTarget))  # show preview of the current image
                return True  # confirm the image is checked
            else:
                if self.makeBell_option.get():
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
            if not self.webcamImage == []:  # check that the image is not empty
                self.processImage(self.webcamImage)
                self.options_image.configure(light_image=Image.fromarray(self.imageTarget))  # show preview of the current image
                return True  # confirm the image is checked
            else:
                if self.makeBell_option.get():
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
            if not self.videoImage == []:  # check that the image is not empty
                self.processImage(self.videoImage)
                self.options_image.configure(light_image=Image.fromarray(self.imageTarget))  # show preview of the current image
                return True  # confirm the image is checked
            else:
                if self.makeBell_option.get():
                    self.bell()
                CTkMessagebox(
                    self,
                    title="Message",
                    message="There is no image, please add an image to the chosen source.",
                    icon="warning",
                    header=True,
                )
                return False  # means there is no image

    def runPytesseract(self):
        if self.checkImage():
            try:
                # Convert image to string
                self.imgToStr = pytesseract.image_to_string(
                    self.imageTarget,
                    config=f'-c page_separator="" --dpi {self.dpi} --psm {self.psm} -c textord_heavy_nr={self.noiseRd_option.get()}',
                )
                self.recognizedText_textBox.configure(state="normal")
                self.recognizedText_textBox.delete("0.0", "end")
                self.recognizedText_textBox.insert("0.0", self.imgToStr)
                self.recognizedText_textBox.configure(state="disabled")
                print(self.imgToStr)

                # Draw bounding boxes and data
                self.results = pytesseract.image_to_data(
                    self.imageTarget,
                    config=f"--dpi {self.dpi} --psm {self.psm} -c textord_heavy_nr={self.noiseRd_option.get()}",
                    output_type=pytesseract.Output.DICT,
                )
                self.imageTarget = cv2.cvtColor(
                    np.asarray(self.imageTarget), cv2.COLOR_RGB2BGR
                )
                for i in range(len(self.results["text"])):
                    # extract the bounding box coordinates of the text region from the current result
                    tmp_tl_x = self.results["left"][i]
                    tmp_tl_y = self.results["top"][i]
                    tmp_br_x = tmp_tl_x + self.results["width"][i]
                    tmp_br_y = tmp_tl_y + self.results["height"][i]
                    tmp_level = self.results["level"][i]

                    if tmp_level == 5:
                        self.imageTarget = cv2.rectangle(
                            self.imageTarget,
                            (tmp_tl_x, tmp_tl_y),
                            (tmp_br_x, tmp_br_y),
                            255,
                            1,
                        )
                self.imageTarget = cv2.cvtColor(self.imageTarget, cv2.COLOR_BGR2RGB)
                self.boundingBoxes_image.configure(
                    light_image=Image.fromarray(self.imageTarget)
                )
                if self.makeBell_option.get():
                    self.bell()
            except Exception as e:
                if self.makeBell_option.get():
                    self.bell()
                CTkMessagebox(
                    self,
                    title="Message",
                    message=f"There was an error while processing text.\n\n{e}",
                    icon="cancel",
                    height=350,
                    header=True,
                )


if __name__ == "__main__":
    app = App()
    app.mainloop()

# When the app is exited by the user, remove the frames folder if it exists, as it is unused

if os.path.isdir("frames"):
    rmtree("frames")