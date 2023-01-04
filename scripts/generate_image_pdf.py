#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageTk
import glob
import numpy as np

import img2pdf
from natsort import natsorted

import tkinter
import tkinter.ttk

class CanvasTrim:
    def __init__(self, canvas:tkinter.Canvas, widht:int, height:int):
        self.rect = None
        self.test_canvas = canvas
        self.CANVAS_WIDTH  = widht
        self.CANVAS_HEIGHT = height
        self.test_canvas.bind('<ButtonPress-1>', self.start_pickup)
        self.test_canvas.bind('<B1-Motion>', self.pickup_position)
        self.select_all()
        
    def start_pickup(self, event):
        if 0 <= event.x <= self.CANVAS_WIDTH and 0 <= event.y <= self.CANVAS_HEIGHT:
            self.rect_start_x = event.x
            self.rect_start_y = event.y

    def pickup_position(self, event):
        if 0 <= event.x <= self.CANVAS_WIDTH and 0 <= event.y <= self.CANVAS_HEIGHT:
            if self.rect:
                self.test_canvas.coords(self.rect,
                    min(self.rect_start_x, event.x), min(self.rect_start_y, event.y),
                    max(self.rect_start_x, event.x), max(self.rect_start_y, event.y))
            else:
                self.rect = self.test_canvas.create_rectangle(self.rect_start_x,
                    self.rect_start_y, event.x, event.y, outline='red')

    def select_all(self):
        if self.rect:
            self.test_canvas.coords(self.rect, 0, 0, self.CANVAS_WIDTH, self.CANVAS_HEIGHT)
        else:
            self.rect = self.test_canvas.create_rectangle(0, 0,
                self.CANVAS_WIDTH, self.CANVAS_HEIGHT, outline='red')
        # x0, y0, x1, y1 = self.test_canvas.coords(self.rect)
        # self.start_x.set('x : ' + str(x0))
        # self.start_y.set('y : ' + str(y0))
        # self.current_x.set('x : ' + str(x1))
        # self.current_y.set('y : ' + str(y1))

    def get_rect(self):
        x0, y0, x1, y1 = self.test_canvas.coords(self.rect)
        return x0, y0, x1, y1


class GenerateImgPdf():
    def __init__(self, current_dir) -> None:
        self._thickness = 1
        image_dir =  current_dir + "/../../Screenshots/"
        self._output_temp_img_path = current_dir + "/../temp/"
        self._output_pdf_path = current_dir + "/../result.pdf"

        files = glob.glob(image_dir + "/**/*.jpg", recursive=True) + glob.glob(image_dir + "/**/*.png", recursive=True) 
        files_sorted = natsorted(files)
        images = []
        # one_width = 0
        # one_height = 0
        for file in files_sorted:
            im = Image.open(file)
            # one_width = max(one_width, im.width)
            # one_height = max(one_height, im.height)
            images.append(im)
        self._images = images
    
    def set_grid(self, row:int, column:int):
        self._row_num = row
        self._columun_num = column
        self._page_num = np.ceil(len(self._images) / (self._columun_num * self._row_num)).astype(int)
        self._header_ratio = 0.2

    def get_sample_img(self):
        return self._images[0]

    def generate(self, x0, y0, x1, y1):

        canvases = self._generate_img(x0, y0, x1, y1)
        img_paths = [] 
        for i, canvas in enumerate(canvases):
            path = self._output_temp_img_path  + "{:02d}.jpg".format(i)
            img_paths.append(path)
            canvas.save(path)

        pdf_bytes = img2pdf.convert(img_paths)
        with open(self._output_pdf_path, "wb") as f:
            f.write(pdf_bytes)

    def _generate_img(self, x0, y0, x1, y1):
        crop_point = (int(x0), int(y0), int(x1), int(y1))
        one_width = crop_point[2] - crop_point[0]
        one_height = crop_point[3] - crop_point[1]
        columun_num = self._columun_num
        row_num = self._row_num
        page_num = self._page_num
        images = self._images
        white = (255, 255, 255)
        black = (0,0,0)

        header_height = int(self._header_ratio * one_height)

        canvas_width = one_width * columun_num + (columun_num -1 ) *self._thickness
        canvas_height = one_height * row_num +  (row_num -1 ) *self._thickness + header_height * 2
        canvases = [Image.new('RGB', (canvas_width, canvas_height), white) for _ in range(page_num)]

        row_frame =  Image.new('RGB', (canvas_width, self._thickness), black)
        column_frame =  Image.new('RGB', (self._thickness, canvas_height - header_height), black)
        for page in range(page_num):
            for row in range(row_num):
                ### 画像配置場所 画像サイズ+枠線分の移動
                paste_y = row * one_height + header_height + row * self._thickness
                if row != 0:
                    ### show row_frame
                    canvases[page].paste(row_frame, (0, paste_y- self._thickness))
                    
                for column in range(columun_num):
                    id = page * row_num * columun_num + row * columun_num + column
                    if id >= len(images):
                        return canvases
                    paste_x = column * one_width + column * self._thickness
                    if column != 0:
                        ### show frame
                        canvases[page].paste(column_frame, (paste_x- self._thickness, header_height))

                    img = images[id]
                    img = img.crop(crop_point)
                    img = img.resize((one_width, one_height))
                    canvases[page].paste(img, (paste_x, paste_y))
    
        return canvases
    
class Application(tkinter.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title('tkinter canvas trial')
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        width = 500
        current_dir = os.path.dirname(__file__)
        self._generate_img_pdf = GenerateImgPdf(current_dir)
        
        image_pil = self._generate_img_pdf.get_sample_img()
        self._scale =  width / image_pil.width
        height =  image_pil.height * self._scale
        image_pil = image_pil.resize((width, int(height)))
        self._image_tk  = ImageTk.PhotoImage(image_pil)
        self.test_canvas = tkinter.Canvas(self, bg="black", width=width, height=height)
        self.test_canvas.grid(row=0, column=0, rowspan=6, padx=10, pady=10)
        self.test_canvas.create_image(0, 0, image=self._image_tk, anchor="nw")
        # self.test_canvas.pack()
        # self.test_canvas = tkinter.Canvas(self, bg='lightblue',
        #     width=width+1, height=height+1,
        #     highlightthickness=0)

        self.label_description1 = tkinter.ttk.Label(self, text='画像をどのように配置するか')
        self.label_description1.grid(row=0, column=1, columnspan=2)

        ui_dir = current_dir + "/../ui/"
        row_path = ui_dir + "icons8-行を表示-80.png"
        column_path = ui_dir + "icons8-列を表示-80.png"
        icon_size = (40,40)
        row_img = Image.open(row_path).resize(icon_size)
        column_img = Image.open(column_path).resize(icon_size)
        self._row_img_tk = ImageTk.PhotoImage(row_img)
        self._column_img_tk = ImageTk.PhotoImage(column_img)
        self._row_img_canvas = tkinter.Canvas(self, bg="white", width=40, height=40)
        self._column_img_canvas = tkinter.Canvas(self, bg="white", width=40, height=40)
        self._row_img_canvas.create_image(1, 1, image=self._row_img_tk, anchor="nw")
        self._column_img_canvas.create_image(1, 1, image=self._column_img_tk, anchor="nw")
        self._row_img_canvas.grid(row=1, column=1)
        self._column_img_canvas.grid(row=2, column=1)
        self._row_num = tkinter.IntVar(value=3)
        self._column_num = tkinter.IntVar(value=2)
        self._entry_row = tkinter.Spinbox(self,textvariable=self._row_num, from_=1, to=100)
        self._entry_column = tkinter.Spinbox(self,textvariable=self._column_num, from_=1, to=100)
        self._entry_row.grid(row = 1, column=2)
        self._entry_column.grid(row = 2, column=2)


        self.label_description = tkinter.ttk.Label(self, text='印刷範囲を選択\r\n(注: 全画像同じトリミングがなされます)')
        self.label_description.grid(row=3, column=1, columnspan=2)
        self._canvas_trim = CanvasTrim(self.test_canvas, width, height)

        self.select_all_button = tkinter.ttk.Button(self, text='全選択', command=self._canvas_trim.select_all)
        self.select_all_button.grid(row=4, column=1, columnspan=2)

        self.select_all_button = tkinter.ttk.Button(self, text='決定', command=self.decide)
        self.select_all_button.grid(row=5, column=1, columnspan=2)
    
    def decide(self):
        row_num = int(self._row_num.get())
        column_num = int(self._column_num.get())
        self._generate_img_pdf.set_grid(row_num, column_num)
        x0, y0, x1, y1 = self._canvas_trim.get_rect()
        self._generate_img_pdf.generate(x0 / self._scale, y0 / self._scale, x1 / self._scale, y1 / self._scale)
        self.master.destroy()

if __name__ == "__main__":
    
    root = tkinter.Tk()
    app = Application(master=root)
    app.mainloop()