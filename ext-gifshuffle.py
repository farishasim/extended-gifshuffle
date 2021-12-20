from os import mkdir, rmdir
import os
import sys
from shutil import rmtree
from typing import Dict, List, Optional
from PIL import Image
import subprocess

BASE_DIR = "dump/"


class GIF:
    def __init__(self) -> None:
        self.data:List[int]
        self.index:Dict = dict()
        return

    def open(self, filename):
        with open(filename, "rb") as f:
            self.data = list(f.read())
            self.indexing()
        
    def indexing(self):
        ptr = 13
        # iterate through all global pallete

        
        return

    def log(self):
        print(self.data)

    def getheader(self):
        return self.data[0:6]
    
    def getscreendesc(self):
        return self.data[6:13]

    def get_global_pallete(self):
        table_size = 1 << ((self.data[10] & 7) + 1)
        print("global table size :", table_size)
        return self.data[13:13+table_size*3]

class StegGIF:
    def getframe(self, filename):
        f = open(filename, "rb")
        data = list(f.read())
        flag = data[10]
        color_size = 1 << ((flag & 7) + 1)
        # remove header & logical descriptor
        # print(data[:13])
        data = data[13:]
        color = data[:color_size*3]
        # print(color)
        data = data[color_size*3:]

        # skip netscape
        exts = data[:27]
        # print(exts)
        data = data[27:]

        desc = data[:10]
        data = data[10:]
        desc[9] = (desc[9] & 0xf8) + (flag & 7)
        desc[9] = desc[9] | 0x80
        
        newdata = []
        newdata.extend(exts)
        newdata.extend(desc)
        newdata.extend(color)
        newdata.extend(data)
        return newdata

    def splitframe(self, filename):
        f = open(filename, "rb")
        data = list(f.read())
        # init pointer
        ptr = 0
        # skip header and global descriptor
        ptr += 13
        global_header = data[:6]
        # skip pallete for frame 1
        color_size = 1 << ((data[10] & 7) + 1)
        ptr += color_size*3
        # skip local extension & descriptor for frame 1
        ptr += 27
        ptr += 10
        # skip lzw minimum code size
        ptr += 1
        while data[ptr] != 0:
            ptr += data[ptr] + 1
        ptr += 1

        frame0 = data[:ptr]
        frame0.append(0x3b)
        mkdir(BASE_DIR+"split")
        open(BASE_DIR+"split/frame-0.gif", "wb").write(bytearray(frame0))

        no_frame = 1
        while data[ptr] != ord(';'):
            # get extensions
            exts = data[ptr:ptr+27]
            transparent_cidx = exts[6]
            ptr += 27
            # get local descriptor
            desc = data[ptr:ptr+10]
            width = desc[5:7]
            heigth = desc[7:9]
            size = desc[9] & 7
            desc[9] = desc[9] & 0x7f
            ptr += 10        

            color_size = (1 << (size + 1)) * 3
            pallete = data[ptr:ptr+color_size]
            ptr += color_size

            start_ptr = ptr
            ptr += 1
            while data[ptr] != 0:
                ptr += data[ptr] + 1
            ptr += 1
            frame_data = data[start_ptr:ptr]

            # add global descriptor for generated gif
            global_desc = []
            global_desc.extend(width)
            global_desc.extend(heigth)
            global_desc.append(0x80 + size)
            global_desc.append(transparent_cidx)
            global_desc.append(0)

            frame = []
            frame.extend(global_header)
            frame.extend(global_desc)
            frame.extend(pallete)
            frame.extend(exts)
            frame.extend(desc)
            frame.extend(frame_data)
            frame.append(0x3b)
            open(BASE_DIR+"split/frame-{}.gif".format(no_frame), "wb").write(bytearray(frame))
            no_frame += 1
        self.n_frame = no_frame
        self.ori_frame = no_frame
        return no_frame

    def hidemsg(self, filename):
        data = open(filename, "rb").read()
        data = list(data)
        # one frame can hide up to 210 bytes
        while len(data) > (self.n_frame * 209):
            self.grow()
        mkdir(BASE_DIR+"out")
        frame = 0
        while len(data) > 0:
            curr = data[:209]
            open(BASE_DIR+"temp.txt", "wb").write(bytearray(curr))
            if frame == 0:
                print("Global Color Table", ":")
            else :
                print("Frame {} Color Table".format(frame), ":")
            # subprocess.run(["gifshuffle", "-S", \
            #                 BASE_DIR+"split/frame-{}.gif".format(frame)])
            subprocess.run(["gifshuffle", "-f", BASE_DIR+"temp.txt", \
                            BASE_DIR+"split/frame-{}.gif".format(frame), \
                            BASE_DIR+"out/frame-{}.gif".format(frame)])
            frame += 1
            data = data[210:]
        
        while frame < self.n_frame:
            subprocess.run(["cp", \
                            BASE_DIR+"split/frame-{}.gif".format(frame), \
                            BASE_DIR+"out/frame-{}.gif".format(frame)])
            frame += 1
        return

    def combine(self, filename="gifs", output="output.gif"):
        with open(BASE_DIR+filename+"/frame-0.gif", "rb") as f:
            data = list(f.read())
            end = data.pop()
            for i in range(1,self.n_frame):
                frame = self.getframe(BASE_DIR+filename+"/frame-{}.gif".format(i))
                data.extend(frame)
                data.pop()
            data.append(end)
            open(output, "wb").write(bytearray(data))

    def grow(self):
        new_frame = self.n_frame
        for i in range(self.ori_frame):
            subprocess.run(["cp", \
                            BASE_DIR+"split/frame-{}.gif".format(i), \
                            BASE_DIR+"split/frame-{}.gif".format(i+new_frame)])
        self.n_frame += self.ori_frame

if __name__ == "__main__":
    # gif = GIF()
    # gif.open("panda.gif")

    # print(gif.getheader())
    # print(gif.getscreendesc())
    # print(gif.get_global_pallete())

    if len(sys.argv) < 3:
        print("usage : python "+sys.argv[0]+" secretfile giffile")

    mkdir(BASE_DIR)

    # normalize gif file
    Image.open(sys.argv[2]).save(BASE_DIR+"opt1.gif", \
                                    save_all=True)
    Image.open(BASE_DIR+"opt1.gif").save(BASE_DIR+"opt2.gif", \
                                    save_all=True)
    Image.open(BASE_DIR+"opt2.gif").save(BASE_DIR+"opt3.gif", \
                                    save_all=True)

    sg = StegGIF()
    n_frames = sg.splitframe(BASE_DIR+"opt3.gif")
    sg.hidemsg(sys.argv[1])
    sg.combine("out", sys.argv[3])

    rmtree(BASE_DIR)