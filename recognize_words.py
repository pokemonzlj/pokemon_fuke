#-*-coding:utf-8-*-

from __future__ import division
import os
import sys
from PIL import Image
#import pytesseract
import time
from datetime import datetime
from PIL import ImageGrab
from pic_contrast_script import contrast_pic

class fuke(contrast_pic):
    def __init__(self,device):
        contrast_pic.__init__(self, device)
        self.device_id=device

    def get_pic(self,id='1163746998'):
        path = os.path.dirname(__file__)+'/pic'
        os.system('adb  -s %s shell screencap -p /sdcard/DCIM/game.png' %id)   #-p: save the file as a png
        os.system('adb  -s %s pull /sdcard/DCIM/game.png %s ' %(id,path) )

    def read_word(self,weizhi='up'):
        '''im.convert()函数解析：
        PIL中有九种不同模式。分别为1，L，P，RGB，RGBA，CMYK，YCbCr，I，F  比如RGB的图片im.getpixel((0,0))会返回RGB三个值(197,111,78)
        im.convert("1")模式“1”为二值图像，非黑即白。但是它每个像素用8个bit表示，0表示黑，255表示白 im.getpixel((0,0))=255
        im.convert("L")模式L”为灰色图像，它的每个像素用8个bit表示，0表示黑，255表示白，其他数字表示不同的灰度，从模式“RGB”转换为“L”模式是按照下面的公式转换的：
          L = R * 299/1000 + G * 587/1000+ B * 114/1000  结果只取整数部分  im.getpixel((0,0))=132
        im.convert("P")模式“P”为8位彩色图像，它的每个像素用8个bit表示，其对应的彩色值是按照调色板查询出来的  im.getpixel((0,0))=62
        im.convert("RGBA")模式“RGBA”为32位彩色图像，它的每个像素用32个bit表示，其中24bit表示红色、绿色和蓝色三个通道，另外8bit表示alpha通道，即透明通道  im.getpixel((0,0))=(197,111,78,255)
        '''
        path = os.path.dirname(__file__)+'/pic'
        pic1_path=path+'/game.png'
        pic=Image.open(pic1_path)
        cut_pic_path=path+'/new.png'
        if weizhi=='up':
            pic.crop((905,526,1050,610)).save(cut_pic_path)  #适用于找到 匹配中 3个字
            pic_new=Image.open(cut_pic_path)
            #word=pytesseract.image_to_string(pic_new, lang='chi_sim')
            pic_new=pic_new.convert('RGBA')
            pix=pic_new.load()
            for y in range(pic_new.size[1]):  # 二值化处理，这个阈值为R=95，G=95，B=95
                for x in range(pic_new.size[0]):   #size[0]即图片长度，size[1]即图片高度
                    if pix[x, y][0] < 26 and 166 <= pix[x, y][1] <= 171 and 239<= pix[x, y][2] <=245 :
                        return 'battle'
            return ''
        elif weizhi=='down':
            pic.crop((820,855,1080,877)).save(cut_pic_path)  #适用于找到 在线匹配 4个字框的上面的一部分
            pic_new=Image.open(cut_pic_path)
            pic_new=pic_new.convert('RGBA')
            pix=pic_new.load()
            # pic_new=pic_new.convert('1')  #convert方法可以将图片转成黑白
            for y in range(pic_new.size[1]):  # 二值化处理，这个阈值为R=95，G=95，B=95
                for x in range(pic_new.size[0]):   #size[0]即图片长度，size[1]即图片高度
                    if pix[x, y][0] ==255 and 198<= pix[x, y][1] <= 202 and pix[x, y][2] <=20:
                        return 'battle'
                    elif 23<= pix[x, y][0] <=27 and 18<= pix[x, y][1] <= 22 and 0 <= pix[x, y][2] <=8:
                        return 'valuebox'
            return ''
        elif weizhi=='level':
            pic.crop((890,905,1020,980)).save(cut_pic_path)  #适用于找到 确定 2个字
            pic_new=Image.open(cut_pic_path)
            pic_new=pic_new.convert('RGBA')
            pix=pic_new.load()
            for y in range(pic_new.size[1]):  # 二值化处理，这个阈值为R=95，G=95，B=95
                for x in range(pic_new.size[0]):   #size[0]即图片长度，size[1]即图片高度
                    if 14 <= pix[x, y][0] <=56 and 160<= pix[x, y][1] <= 174 and 238 <= pix[x, y][2] <=248:
                        return 'OK'
            return ''


    def duizhan_battle(self,id='1163746998'):
        for i in range(300):
            os.system("adb -s %s shell input tap 953 872" %id)  #点在线匹配
            time.sleep(5)  #刚开始匹配多等一会
            self.get_pic(id)
            str1='battle'
            count=0
            while str1 in self.read_word('up') and count<17:  #当可以检测到匹配中时
                time.sleep(3)  #每3秒截屏
                self.get_pic(id)
                count+=1
            if count==17:
                os.system("adb -s %s shell input tap 950 568"  %id) #点击取消
                print 'No match anyone in 1 min, rematch'
                time.sleep(1)
                continue  #退出当次循环，从新开始匹配
            os.system("adb -s %s shell input tap 945 532"  %id)  #点击开始
            print 'start matching'
            for i in range(40):
                time.sleep(10) #2分钟对战
                self.get_pic(id)
                if self.read_word('level')=='OK':
                    print 'Battle end'
                    os.system("adb -s %s shell input tap 956 946"  %id)  #点击升阶确定
                    print 'click comfirm reward button'
                    time.sleep(2)
                    self.get_pic(id)
                    if not str1 in self.read_word('down'):#可能会有宝箱界面
                        os.system("adb -s %s shell input tap 1023 572"  %id)   #宝箱位置
                        print 'click valueable box'
                        time.sleep(3)
                        path=os.path.dirname(__file__)+'/pic'
                        timepic=datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
                        os.system('adb  -s %s shell screencap -p /sdcard/DCIM/%s.png' %(id,timepic) )  #掉出宝箱之后截图以便查看
                        os.system('adb  -s %s pull /sdcard/DCIM/%s.png %s ' %(id,timepic,path) )
                        print 'after win, save screenshot about valuebox'
                        os.system("adb -s %s shell input tap 950 900"  %id)  #确定
                        print 'click confirm button'
                        time.sleep(1)
                    break
                elif self.read_word('down')==str1:
                    print 'Battle end'
                    break
                elif self.read_word('down')=='valuebox':
                    os.system("adb -s %s shell input tap 1023 572"  %id)   #宝箱位置
                    print 'click valueable box'
                    time.sleep(3)
                    path=os.path.dirname(__file__)+'/pic'
                    timepic=datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
                    os.system('adb  -s %s shell screencap -p /sdcard/DCIM/%s.png' %(id,timepic) )  #掉出宝箱之后截图以便查看
                    os.system('adb  -s %s pull /sdcard/DCIM/%s.png %s ' %(id,timepic,path) )
                    print 'after lost, save screenshot about valuebox'
                    os.system("adb -s %s shell input tap 950 900"  %id)  #确定
                    print 'click confirm button'
                    time.sleep(1)
                    break

    def shilian(self,yuangu=True):
        self.get_screenshot()
        self.cut_pic((1785,285),(1860,370))  #80*85的图片
        # path = os.path.dirname(__file__)+'/pic'
        # pic_path=path+'/screenshot.png'
        # pic_black_path=path+'/cut.png'
        if self.contrast_black_pic('shilian')==True:
            self.click(1800,330)
            self.delay(2)
        for i in range(5):
            self.get_screenshot()
            self.cut_pic((750,360),(1140,415))  #截取正中间图标上面的标题一栏
            if self.contrast_black_pic('shanguang')==True:  #闪光试炼
                self.click(950,600)  #点中间的图标进去
                self.delay(2)
                self.click(950,600)  #点中间的图标进去
                self.delay(2)
                self.click(1400,700)  #点难度4
                self.delay(2)
            else:
                self.click(480,600)  #点左边的图标切换
                self.delay(2)

    def tiaozhan(self):
        '''每日等待自动弹出来的PVP邀请'''
        for i in range(100000):
            self.get_screenshot()
            self.cut_pic((520,580),(1450,810))
            zuanshi=0
            if self.contrast_black_pic('tiaozhan')==True:
                self.click(770,750)   #点击确认接受挑战
                self.delay(4)
                self.get_screenshot()
                self.cut_pic((820,870),(1100,950))  #在线匹配的图标
                while self.contrast_black_pic('zaixianpipei')==True:   #当依然能找到在线匹配图标的时候
                    self.delay(3)
                    self.get_screenshot()
                    self.cut_pic((820,870),(1100,950)) #在线匹配的图标
                self.click(945,532)   #点击开始
                self.delay(4)
                self.get_screenshot()
                self.cut_pic((1750,880),(1900,1060))  #逃跑的图标
                while self.contrast_black_pic('taopao')==False:
                    self.delay(3)
                    self.get_screenshot()
                    self.cut_pic((1750,880),(1900,1060))  #逃跑的图标
                self.click(1820,965)  #点击逃跑
                self.delay(2)
                self.click(790,610)  #点击确定
                self.delay(5)
                self.click(1850,60)  #点击关闭按钮退出PVP界面
                zuanshi+=5
                print 'have got %s diamond!' %zuanshi
            self.delay(3)

    def get(self):
        self.get_screenshot()
        self.cut_pic((1750,880),(1900,1060))



if __name__ == '__main__':
    test=fuke('1163746998')
    #test.get()
    #read_word('up')
    #test.duizhan_battle()
    #test.shilian()
    test.tiaozhan()