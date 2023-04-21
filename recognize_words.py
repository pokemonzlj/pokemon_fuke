# -*-coding:utf-8-*-
import os
import sys
from PIL import Image
import pytesseract
import time
import threading
import _thread
from datetime import datetime
from PIL import ImageGrab
from pic_contrast_script import contrast_pic
import math
import subprocess
import re


class myThread(threading.Thread):  # 继承父类threading.Thread
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter

    def run(self):  # 把要执行的代码写到run函数里面 线程在创建后会直接运行run函数
        print("Starting " + self.name)
        print_time(self.name, self.counter, 5)
        print("Exiting " + self.name)


class fuke(contrast_pic):
    def __init__(self, device):
        '''游戏屏幕都是1920*1080
        但是打开百度会有导航栏，导致屏幕变成了1768*1080，所以要对X轴做一个同比例调整'''
        contrast_pic.__init__(self, device)
        self.device_id = device
        self.ratio = 2340 / 1920  # T1的Y轴对比正常1920的分辨率
        self.distance = 355  # T1额外平移X轴的距离
        self.bili = 1
        self.extra_distance = 0
        self.zhanli_repeat = 0

    def get_pic(self, id='1163746998'):
        # path = os.path.dirname(__file__)+'/pic'
        # subprocess.Popen('adb  -s %s shell screencap -p /sdcard/DCIM/screenshot.png' %id).wait()   #-p: save the file as a png
        # os.system('adb  -s %s pull /sdcard/DCIM/screenshot.png %s ' %(id,path) )
        # os.system('adb  -s %s shell rm /sdcard/DCIM/screenshot.png' %id).wait()
        path = os.path.dirname(__file__) + '/pic'
        timepic = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        subprocess.Popen(
            'adb  -s %s shell screencap -p /sdcard/DCIM/screenshot.png' % (self.device_id)).wait()  # 掉出宝箱之后截图以便查看
        subprocess.Popen('adb  -s %s pull /sdcard/DCIM/screenshot.png %s/%s.png ' % (self.device_id, path, timepic),
                         stdout=subprocess.PIPE).wait()
        print("Get reward screenshot")
        subprocess.Popen('adb  -s %s shell rm /sdcard/DCIM/screenshot.png' % id).wait()

    def check_package(self, id='1163746998'):
        r = os.popen("adb -s %s shell dumpsys window | findstr mCurrentFocus" % id,
                     "r")  # 想获取控制台输出的内容，那就用os.popen的方法了，popen返回的是一个file对象，跟open打开文件一样操作了，r是以读的方式打开
        # dumpsys activity top|grep ACTIVITY
        string = r.read()  # 返回file对象后再去read
        if "com.pocketmon.baidu" in string:
            print("It's baidu game, the resolution is 1768*1080")
            self.bili = self.ratio
            return True
        else:
            print("It's not baidu game, the resolution is 1920*1080")
            self.bili = 1
            return False

    def read_word(self, weizhi='up'):
        '''im.convert()函数解析：
        PIL中有九种不同模式。分别为1，L，P，RGB，RGBA，CMYK，YCbCr，I，F  比如RGB的图片im.getpixel((0,0))会返回RGB三个值(197,111,78)
        im.convert("1")模式“1”为二值图像，非黑即白。但是它每个像素用8个bit表示，0表示黑，255表示白 im.getpixel((0,0))=255
        im.convert("L")模式L”为灰色图像，它的每个像素用8个bit表示，0表示黑，255表示白，其他数字表示不同的灰度，从模式“RGB”转换为“L”模式是按照下面的公式转换的：
          L = R * 299/1000 + G * 587/1000+ B * 114/1000  结果只取整数部分  im.getpixel((0,0))=132
        im.convert("P")模式“P”为8位彩色图像，它的每个像素用8个bit表示，其对应的彩色值是按照调色板查询出来的  im.getpixel((0,0))=62
        im.convert("RGBA")模式“RGBA”为32位彩色图像，它的每个像素用32个bit表示，其中24bit表示红色、绿色和蓝色三个通道，另外8bit表示alpha通道，即透明通道  im.getpixel((0,0))=(197,111,78,255)
        '''
        path = os.path.dirname(__file__) + '/pic'
        pic1_path = path + '/screenshot.png'
        pic = Image.open(pic1_path)
        cut_pic_path = path + '/cut.png'
        # if self.check_package()==True:
        #     bili=self.ratio
        # else:
        #     bili=1
        if weizhi == 'up':
            pic.crop((int(905 * self.bili + self.extra_distance), 526, int(1050 * self.bili + self.extra_distance),
                      610)).save(cut_pic_path)  # 适用于找到 匹配中 3个字
            pic_new = Image.open(cut_pic_path)
            # word=pytesseract.image_to_string(pic_new, lang='chi_sim')
            pic_new = pic_new.convert('RGBA')
            pix = pic_new.load()
            for y in range(pic_new.size[1]):  # 二值化处理，这个阈值为R=95，G=95，B=95
                for x in range(pic_new.size[0]):  # size[0]即图片长度，size[1]即图片高度
                    if pix[x, y][0] < 26 and 166 <= pix[x, y][1] <= 171 and 239 <= pix[x, y][2] <= 245:
                        return 'battle'
            return ''
        elif weizhi == 'down':
            pic.crop((int(840 * self.bili + self.extra_distance), 950, int(950 * self.bili + self.extra_distance),
                      960)).save(cut_pic_path)  # 适用于找到 在线匹配 4个字框的下面的左半边部分
            pic_new = Image.open(cut_pic_path)
            pic_new = pic_new.convert('RGBA')
            pix = pic_new.load()
            # pic_new=pic_new.convert('1')  #convert方法可以将图片转成黑白
            for y in range(pic_new.size[1]):  # 二值化处理，这个阈值为R=95，G=95，B=95
                for x in range(pic_new.size[0]):  # size[0]即图片长度，size[1]即图片高度
                    if 250<= pix[x, y][0] <= 255 and 195 <= pix[x, y][1] <= 202 and pix[x, y][2] <= 18: # 接近纯土黄色
                        return 'battle'
                    elif 22 <= pix[x, y][0] <= 30 and 16 <= pix[x, y][1] <= 24 and pix[x, y][2] <= 5:  # 有宝箱界面遮挡
                        return 'valuebox'
            return ''
        elif weizhi == 'level':
            pic.crop((int(890 * self.bili + self.extra_distance), 905, int(1020 * self.bili + self.extra_distance),
                      980)).save(cut_pic_path)  # 适用于找到 确定 2个字
            pic_new = Image.open(cut_pic_path)
            pic_new = pic_new.convert('RGBA')
            pix = pic_new.load()
            for y in range(pic_new.size[1]):  # 二值化处理，这个阈值为R=95，G=95，B=95
                for x in range(pic_new.size[0]):  # size[0]即图片长度，size[1]即图片高度
                    if 14 <= pix[x, y][0] <= 56 and 160 <= pix[x, y][1] <= 174 and 238 <= pix[x, y][2] <= 248:
                        return 'OK'
            return ''
        elif weizhi == 'taopao':
            pic.crop((int(870 * self.bili + self.extra_distance), 570, int(1050 * self.bili + self.extra_distance),
                      630)).save(cut_pic_path)  # 适用于找到 （对方已经逃跑）我知道啦 4个字
            pic_new = Image.open(cut_pic_path)
            pic_new = pic_new.convert('RGBA')
            pix = pic_new.load()
            for y in range(pic_new.size[1]):  # 二值化处理，这个阈值为R=95，G=95，B=95
                for x in range(pic_new.size[0]):  # size[0]即图片长度，size[1]即图片高度
                    if 14 <= pix[x, y][0] <= 56 and 160 <= pix[x, y][1] <= 174 and 238 <= pix[x, y][2] <= 248:
                        return 'OK'
            return ''
        elif weizhi == 'qiangkuang3':
            pic.crop((int(1333 * self.bili + self.extra_distance), 637, int(1426 * self.bili + self.extra_distance),
                      690)).save(cut_pic_path)  # 适用于找到 右下角的蓝旗
            pic_new = Image.open(cut_pic_path)
            pic_new = pic_new.convert('RGBA')
            pix = pic_new.load()
            # pic_new=pic_new.convert('1')  #convert方法可以将图片转成黑白
            for y in range(pic_new.size[1]):  # 二值化处理，这个阈值为R=95，G=95，B=95
                for x in range(pic_new.size[0]):  # size[0]即图片长度，size[1]即图片高度
                    if 30 <= pix[x, y][0] <= 50 and 119 <= pix[x, y][1] <= 142 and 200 <= pix[x, y][2] <= 224:
                        return True
            return False
        elif weizhi == 'qiangkuang2':
            pic.crop((int(576 * self.bili + self.extra_distance), 637, int(677 * self.bili + self.extra_distance),
                      690)).save(cut_pic_path)  # 适用于找到 左下角的蓝旗
            pic_new = Image.open(cut_pic_path)
            pic_new = pic_new.convert('RGBA')
            pix = pic_new.load()
            # pic_new=pic_new.convert('1')  #convert方法可以将图片转成黑白
            for y in range(pic_new.size[1]):  # 二值化处理，这个阈值为R=95，G=95，B=95
                for x in range(pic_new.size[0]):  # size[0]即图片长度，size[1]即图片高度
                    if 30 <= pix[x, y][0] <= 50 and 119 <= pix[x, y][1] <= 142 and 200 <= pix[x, y][2] <= 224:
                        return True
            return False
        elif weizhi == 'qiangkuang1':
            pic.crop((int(957 * self.bili + self.extra_distance), 400, int(1054 * self.bili + self.extra_distance),
                      452)).save(cut_pic_path)  # 适用于找到 顶端的蓝旗
            pic_new = Image.open(cut_pic_path)
            pic_new = pic_new.convert('RGBA')
            pix = pic_new.load()
            # pic_new=pic_new.convert('1')  #convert方法可以将图片转成黑白
            for y in range(pic_new.size[1]):  # 二值化处理，这个阈值为R=95，G=95，B=95
                for x in range(pic_new.size[0]):  # size[0]即图片长度，size[1]即图片高度
                    if 30 <= pix[x, y][0] <= 50 and 119 <= pix[x, y][1] <= 142 and 200 <= pix[x, y][2] <= 224:
                        return True
            return False
        elif weizhi == 'qiangkuang_zhanli':
            # pic.crop((int(670*self.bili+self.extra_distance),740,int(825*self.bili+self.extra_distance),785)).save(cut_pic_path)  #适用于找到 战斗力的数值
            pic.crop((int(665 * self.bili + self.extra_distance), 825, int(830 * self.bili + self.extra_distance),
                      880)).save(cut_pic_path)  # 适用于找到 战斗力的数值
            pic_new = Image.open(cut_pic_path)  # .convert('RGB')
            word = pytesseract.image_to_string(pic_new)  # , lang='chi_sim',config="-psm 6"
            word = word.strip()  # 识别出的结果总是带有向上的箭头在这里插入图片描述和很多的换行符,.strip()移除字符串头尾指定的字符（默认为空格或换行符）
            # print(word)
            if word != "" and word != None and word.isdigit():
                # print("is%s!"%word
                # print("type is %s."%(type(word))
                return word
            elif self.zhanli_repeat < 10:
                print("Can not read the zhanli, refind it! Now zhanli repeat time is:%s" % (self.zhanli_repeat + 1))
                self.get_screenshot()
                self.zhanli_repeat += 1
                self.read_word('qiangkuang_zhanli')
            else:
                return 99999
        elif weizhi == 'qiangkuang_jiangli':
            pic.crop((int(872 * self.bili + self.extra_distance), 862, int(1045 * self.bili + self.extra_distance),
                      878)).save(cut_pic_path)  # 适用于找到 打完整个抢矿后弹出的奖励界面的 确定 图标,为了跟战斗的确定区分开，只取图标的上面一小块
            pic_new = Image.open(cut_pic_path)
            pic_new = pic_new.convert('RGBA')
            pix = pic_new.load()
            # pic_new=pic_new.convert('1')  #convert方法可以将图片转成黑白
            for y in range(pic_new.size[1]):  # 二值化处理，这个阈值为R=95，G=95，B=95
                for x in range(pic_new.size[0]):  # size[0]即图片长度，size[1]即图片高度
                    if 6 <= pix[x, y][0] <= 35 and 152 <= pix[x, y][1] <= 174 and 235 <= pix[x, y][2] <= 250:
                        return True
            return False
        elif weizhi == 'zidong':
            pic.crop((int(1745 * self.bili + self.extra_distance), 50, int(1810 * self.bili + self.extra_distance),
                      70)).save(cut_pic_path)  # 适用于找到 切换自动战斗的咖啡色小图标
            pic_new = Image.open(cut_pic_path)
            pic_new = pic_new.convert('RGBA')
            pix = pic_new.load()
            # pic_new=pic_new.convert('1')  #convert方法可以将图片转成黑白
            for y in range(pic_new.size[1]):  # 二值化处理，这个阈值为R=95，G=95，B=95
                for x in range(pic_new.size[0]):  # size[0]即图片长度，size[1]即图片高度
                    if 55 <= pix[x, y][0] <= 72 and 24 <= pix[x, y][1] <= 36 and 4 <= pix[x, y][2] <= 22:
                        return True
            return False
        elif weizhi == 'chuzhan':  # 选择出战精灵
            pic.crop((int(1570 * self.bili + self.extra_distance), 271, int(1700 * self.bili + self.extra_distance),
                      283)).save(cut_pic_path)  # 适用于找到 出战精灵队伍选择的确定框
            pic_new = Image.open(cut_pic_path)
            pic_new = pic_new.convert('RGBA')
            pix = pic_new.load()
            # pic_new=pic_new.convert('1')  #convert方法可以将图片转成黑白
            for y in range(pic_new.size[1]):  # 二值化处理，这个阈值为R=95，G=95，B=95
                for x in range(pic_new.size[0]):  # size[0]即图片长度，size[1]即图片高度
                    if 6 <= pix[x, y][0] <= 30 and 158 <= pix[x, y][1] <= 174 and 236 <= pix[x, y][2] <= 252:
                        return True
            return False
        elif weizhi == 'hailuo':  # 保母曼波的海螺结算界面
            pic.crop((int(870 * self.bili + self.extra_distance), 755, int(1045 * self.bili + self.extra_distance),
                      770)).save(cut_pic_path)
            pic_new = Image.open(cut_pic_path)
            pic_new = pic_new.convert('RGBA')
            pix = pic_new.load()
            # pic_new=pic_new.convert('1')  #convert方法可以将图片转成黑白
            for y in range(pic_new.size[1]):  # 二值化处理，这个阈值为R=95，G=95，B=95
                for x in range(pic_new.size[0]):  # size[0]即图片长度，size[1]即图片高度
                    if 56 <= pix[x, y][0] <= 62 and 239 <= pix[x, y][1] <= 250 and 250 <= pix[x, y][2] <= 255:
                        return True
            return False
        elif weizhi == 'zhanbu':  # 每日首胜的占卜界面
            pic_new = Image.open(pic1_path)
            pic_new = pic_new.convert('RGBA')
            pix = pic_new.load()
            for x in range(int(1210 * self.bili + self.extra_distance),
                           int(1450 * self.bili + self.extra_distance)):  # size[0]即图片长度，size[1]即图片高度
                if 245 <= pix[x, 780][0] <= 255 and 223 <= pix[x, 780][1] <= 233 and 102 <= pix[x, 780][2] <= 112:
                    return True
            return False
        # elif weizhi=='gangsi_fenshu':
        #     pic.crop((int(1100*self.bili+self.extra_distance),360,int(1200*self.bili+self.extra_distance),400)).save(cut_pic_path)  #适用于找到 挑战积分的数值
        #     pic_new=Image.open(cut_pic_path)#.convert('RGB')
        #     word=pytesseract.image_to_string(pic_new)#, lang='chi_sim'
        #     if word != "" and word !=None:
        #         #print("is%s!"%word
        #         #print("type is %s."%(type(word))
        #         return word
        #     else:
        #         print("Can not read the score, refind it!"
        #         self.get_screenshot()
        #         self.read_word('gangsi_fenshu')
        # elif weizhi=='gangsi_jieshu':  #走钢丝结算界面
        #     pic.crop((int(870*self.bili+self.extra_distance),690,int(1000*self.bili+self.extra_distance),700)).save(cut_pic_path)  #适用于找到 走钢丝领取奖励的确定框
        #     pic_new=Image.open(cut_pic_path)
        #     pic_new=pic_new.convert('RGBA')
        #     pix=pic_new.load()
        #     # pic_new=pic_new.convert('1')  #convert方法可以将图片转成黑白
        #     for y in range(pic_new.size[1]):  # 二值化处理，这个阈值为R=95，G=95，B=95
        #         for x in range(pic_new.size[0]):   #size[0]即图片长度，size[1]即图片高度
        #             if  pix[x, y][0] <=14 and 154<= pix[x, y][1] <= 168 and 238<=pix[x, y][2] <=256:
        #                 return True
        #     return False
        # elif weizhi=='gangsi_gunzi':  #走钢丝结算界面
        #     # pic.crop((int(870*self.bili+self.extra_distance),690,int(1000*self.bili+self.extra_distance),700)).save(cut_pic_path)  #适用于找到 走钢丝领取奖励的确定框
        #     pic_new=Image.open(pic1_path)
        #     pic_new=pic_new.convert('RGBA')
        #     pix=pic_new.load()
        #     # pic_new=pic_new.convert('1')  #convert方法可以将图片转成黑白
        #     # for y in range(pic_new.size[1]):  # 二值化处理，这个阈值为R=95，G=95，B=95
        #     for x in range(130,330):   #size[0]即图片长度，size[1]即图片高度
        #         if  180<=pix[x, 758][0] <=212 and 48<= pix[x, 758][1] <= 84 and 80<=pix[x, 758][2] <=114:
        #             return x
        #     return False
        # elif weizhi=='gangsi_taozi':  #走钢丝结算界面
        #     # pic.crop((int(870*self.bili+self.extra_distance),690,int(1000*self.bili+self.extra_distance),700)).save(cut_pic_path)  #适用于找到 走钢丝领取奖励的确定框
        #     pic_new=Image.open(pic1_path)
        #     pic_new=pic_new.convert('RGBA')
        #     pix=pic_new.load()
        #     # pic_new=pic_new.convert('1')  #convert方法可以将图片转成黑白
        #     # for y in range(pic_new.size[1]):  # 二值化处理，这个阈值为R=95，G=95，B=95
        #     for x in range(360,1600):   #size[0]即图片长度，size[1]即图片高度
        #         if  230<=pix[x, 751][0] <=255 and 120<= pix[x, 751][1] <= 138 and 142<=pix[x, 751][2] <=164:
        #             return x
        #     return False

    def duizhan_battle(self, id='1163746998'):
        # if self.check_package()==True:
        #     bili=self.ratio
        # else:
        #     bili=1
        for i in range(300):
            x = int(950 * self.bili + self.extra_distance)
            os.system("adb -s %s shell input tap %s 872" % (id, x))  # 点在线匹配
            print("Click start matching.")
            time.sleep(5)  # 刚开始匹配多等一会
            self.get_screenshot('pic')
            str1 = 'battle'
            count = 0
            while str1 in self.read_word('up') and count < 17:  # 当可以检测到匹配中时
                time.sleep(3)  # 每3秒截屏
                self.get_screenshot('pic')
                count += 1
            if count == 17:
                os.system("adb -s %s shell input tap %s 568" % (id, x))  # 点击取消
                print('No match anyone in 1 min, rematch')
                time.sleep(1)
                continue  # 退出当次循环，从新开始匹配
            os.system("adb -s %s shell input tap %s 532" % (id, x))  # 点击开始
            print('Find opponent,start fighting!')
            for i in range(40):
                time.sleep(10)  # 2分钟对战
                self.get_screenshot('pic')
                if self.read_word('taopao') == 'OK' and self.read_word('down') != 'valuebox':  # 逃跑跟钻石箱子蓝色相同。增加一层判断
                    self.click(int(910 * self.bili + self.extra_distance), 600)
                    # os.system("adb -s %s shell input tap 766 711"  %id)  #点击 我知道啦
                    print("The opposite guy has run away!")
                    self.delay(2)
                    self.get_screenshot('pic')
                if self.read_word('level') == 'OK':
                    print('Battle end')
                    os.system("adb -s %s shell input tap %s 946" % (id, x))  # 点击升阶确定
                    print('Click comfirm reward button')
                    time.sleep(2)
                    self.get_screenshot('pic')
                    # if self.read_word('hailuo')==True:
                    #     os.system("adb -s %s shell input tap %s 762"  %(id, x))  #点击海螺确定界面
                    #     print ("Click close hailuo screen.")
                    #     time.sleep(2)
                    #     self.get_screenshot('pic')
                    if self.read_word('down') == 'valuebox':  # 可能会有宝箱界面
                        os.system("adb -s %s shell input tap %s 572" % (id, x))  # 宝箱位置
                        print('Click valueable box')
                        time.sleep(3)
                        print('After win, save screenshot about valuebox.')
                        self.get_pic(id)
                        os.system("adb -s %s shell input tap %s 900" % (id, x))  # 确定
                        print('Click confirm button')
                        time.sleep(2)
                        self.get_screenshot('pic')
                    if self.read_word('zhanbu') == True:
                        x_right = int(1320 * self.bili + self.extra_distance)
                        os.system("adb -s %s shell input tap %s 813" % (id, x_right))  # 点击占卜图标
                        print("Click zhanbu button.")
                        time.sleep(3)
                        os.system("adb -s %s shell input tap %s 900" % (id, x))  # 点击确定图标
                        print("Click confirm the reward.")
                        time.sleep(2)
                        x_right = int(1660 * self.bili + self.extra_distance)
                        os.system("adb -s %s shell input tap %s 120" % (id, x_right))  # 点击关闭占卜界面
                        print("Click close zhanbu screen.")
                        time.sleep(2)
                        self.get_screenshot('pic')
                        if self.read_word('level') == 'OK':
                            print('Battle end')
                            os.system("adb -s %s shell input tap %s 946" % (id, x))  # 点击升阶确定
                            print('Click comfirm reward button')
                            time.sleep(2)
                        break
                    break
                elif self.read_word('hailuo') == True:
                    os.system("adb -s %s shell input tap %s 762" % (id, x))  # 点击海螺确定界面
                    print("Click close hailuo screen.")
                    time.sleep(1)
                    self.get_screenshot('pic')
                    if self.read_word('down') == str1:
                        print('Battle end')
                        break
                    elif self.read_word('down') == 'valuebox':
                        os.system("adb -s %s shell input tap %s 572" % (id, x))  # 宝箱位置
                        print('Click valueable box')
                        time.sleep(3)
                        self.get_pic(id)
                        print('After lost, save screenshot about valuebox.')
                        os.system("adb -s %s shell input tap %s 900" % (id, x))  # 确定
                        print('Click confirm button')
                        time.sleep(1)
                        break
                elif self.read_word('down') == str1:
                    print('Battle end')
                    break
                elif self.read_word('down') == 'valuebox':
                    os.system("adb -s %s shell input tap %s 572" % (id, x))  # 宝箱位置
                    print('Click valueable box')
                    time.sleep(3)
                    self.get_pic(id)
                    print('After lost, save screenshot about valuebox.')
                    os.system("adb -s %s shell input tap %s 900" % (id, x))  # 确定
                    print('Click confirm button')
                    time.sleep(1)
                    break

    def shilian(self, yuangu=True):
        self.get_screenshot()
        self.cut_pic((1785, 285), (1860, 370))  # 80*85的图片
        # path = os.path.dirname(__file__)+'/pic'
        # pic_path=path+'/screenshot.png'
        # pic_black_path=path+'/cut.png'
        if self.contrast_black_pic('shilian') == True:
            self.click(1800, 330)
            self.delay(2)
        for i in range(5):
            self.get_screenshot()
            self.cut_pic((750, 360), (1140, 415))  # 截取正中间图标上面的标题一栏
            if self.contrast_black_pic('shanguang') == True:  # 闪光试炼
                self.click(950, 600)  # 点中间的图标进去
                self.delay(2)
                self.click(950, 600)  # 点中间的图标进去
                self.delay(2)
                self.click(1400, 700)  # 点难度4
                self.delay(2)
            else:
                self.click(480, 600)  # 点左边的图标切换
                self.delay(2)

    def tiaozhan(self):
        """每日等待自动弹出来的PVP邀请"""
        for i in range(100000):
            self.get_screenshot()
            self.cut_pic((520, 580), (1450, 810))
            zuanshi = 0
            if self.contrast_black_pic('tiaozhan') == True:
                self.click(770, 750)  # 点击确认接受挑战
                self.delay(4)
                self.get_screenshot()
                self.cut_pic((820, 870), (1100, 950))  # 在线匹配的图标
                while self.contrast_black_pic('zaixianpipei') == True:  # 当依然能找到在线匹配图标的时候
                    self.delay(3)
                    self.get_screenshot()
                    self.cut_pic((820, 870), (1100, 950))  # 在线匹配的图标
                self.click(945, 532)  # 点击开始
                self.delay(4)
                self.get_screenshot()
                self.cut_pic((1750, 880), (1900, 1060))  # 逃跑的图标
                while self.contrast_black_pic('taopao') == False:
                    self.delay(3)
                    self.get_screenshot()
                    self.cut_pic((1750, 880), (1900, 1060))  # 逃跑的图标
                self.click(1820, 965)  # 点击逃跑
                self.delay(2)
                self.click(790, 610)  # 点击确定
                self.delay(5)
                self.click(1850, 60)  # 点击关闭按钮退出PVP界面
                zuanshi += 5
                print('have got %s diamond!' % zuanshi)
            self.delay(3)

    def geti(self):
        for i in range(60):
            self.click(int(1711 * self.bili + self.extra_distance), 910)
            self.delay(1)
            self.click(int(938 * self.bili + self.extra_distance), 729)
            self.delay(1)
            self.click(int(794 * self.bili + self.extra_distance), 644)
            print('click %s time' % (i + 1))
            self.delay(300)

    def start_game(self, account='baidu'):
        '''利用adb shell dumpsys SurfaceFlinger 或者 adb shell-> dumpsys activity | grep -i run查看当前运行进程'''
        if account == 'baidu':
            os.system("adb  -s %s shell am start com.pocketmon.baidu.gh/com.pocketmon.baidu.AppEntry" % self.device_id)
        elif account == 'xiaomi':
            os.system("adb -s %s shell am start com.pocketmon.mi/.AppEntry" % self.device_id)
        elif account == 'guanfang':
            os.system("adb -s %s shell am start com.Pocketmon.ay/.AppEntry" % self.device_id)
        self.delay(30)
        for i in range(10):
            self.get_screenshot()
            self.cut_pic((867, 899), (1009, 967))  # 通知信息 确定的图标
            if self.contrast_black_pic('queding'):
                self.click(920, 930)  # 通知确定
                break
            else:
                self.back()
                self.delay(2)
                self.get_screenshot()
                self.cut_pic((750, 450), (1140, 500))  # 确定退出提示框
                if self.contrast_black_pic('quedingtuichu'):
                    self.click(780, 700)  # 取消退出
                    self.delay(1)
            self.delay(5)
        for i in range(10):
            self.delay(5)
            self.get_screenshot()
            self.cut_pic((794, 771), (893, 815))  # 区服的图标
            if self.contrast_black_pic('qvfu1') or self.contrast_black_pic('qvfu2'):
                self.click(940, 950)  # 进入游戏
                break

    def qiangkuang_judge(self):
        self.get_screenshot()
        if self.read_word('qiangkuang3') == True:
            print("Find 3 opponents!")
            return 3
        elif self.read_word('qiangkuang2') == True:
            print("Find 2 opponents!")
            return 2
        elif self.read_word('qiangkuang1') == True:
            print("Find 1 opponent!")
            return 1
        else:
            print("Can not find any kuang!")
            return False

    def qiangkuang_battle(self, power=400000):
        self.get_screenshot('pic')
        self.zhanli_repeat = 0
        zhanli = self.read_word('qiangkuang_zhanli')
        zhanli = int(zhanli)
        # if self.check_package()==True:
        #     bili=self.ratio
        # else:
        #     bili=1
        if zhanli < power:  # 只打战力小于设定值power的对手
            print("combat effectiveness is %s, start robbing!" % zhanli)
            self.click(int(1475 * self.bili + self.extra_distance), 263)  # 点击抢夺
            self.delay(5)
            for i in range(5):
                self.get_screenshot('pic')
                if self.read_word('chuzhan') == True:  # 如果找到出战精灵选择界面
                    # self.click(1620,280)
                    break
                else:
                    self.delay(5)
            self.click(int(1637 * self.bili + self.extra_distance), 493)  # 选择编队1
            self.delay(2)
            self.click(int(1630 * self.bili + self.extra_distance), 315)  # 点击确定,战斗完后等待5秒就会自动退出战斗结束界面
            self.delay(5)  # 等待进入战斗
            self.get_screenshot('pic')
            if self.read_word('zidong') == True:
                print("Switch to auto battle mode.")
                self.click(int(1770 * self.bili + self.extra_distance), 70)  # 点击切换
            self.delay(20)
            for i in range(10):
                self.get_screenshot('pic')
                if self.read_word('qiangkuang_jiangli') == True:  # 如果是一面旗的情况，打完等待显示奖励界面
                    self.get_pic(self.device_id)
                    print("Save reward pic.")
                    self.click(int(955 * self.bili + self.extra_distance), 910)
                    return 'OK'
                elif self.read_word('qiangkuang1') == True:  # 如果是多面旗的情况，战斗完成后如果重新可见顶端的小蓝旗，则完成战斗
                    print("Still have other kuang for robbing!")
                    break
                else:
                    self.delay(10)
            return True
        else:
            print("the opponent's combat effectiveness is %s too high, rematch!" % zhanli)
            self.click(int(1645 * self.bili + self.extra_distance), 171)  # 点击退出
            return False
            # self.click(int(1738*self.bili+self.extra_distance),940)   #点击重新搜索
            # return False
        # pass

    def qiangkuang(self, power=400000):
        # if self.check_package()==True:
        #     bili=self.ratio
        # else:
        #     bili=1
        for i in range(300):  # 只抢3人防守的矿
            judge = self.qiangkuang_judge()
            if judge == False:
                self.click(int(1370 * self.bili + self.extra_distance), 490)  # 点击抢矿的大图标
                print("Click start robbing button")
                self.delay(5)  # 等待进入抢矿的界面
                self.get_screenshot('pic')
                self.cut_pic((int(1306 * self.bili + self.extra_distance), 325),
                             (int(1454 * self.bili + self.extra_distance), 495))  # 抢矿的大图标
                # self.cut_pic((int(1306*self.bili+self.extra_distance),325),(int(1454*self.bili+self.extra_distance),495))
                if self.contrast_grey_pic('kuang') == True:  # 要是抢矿的图标依然存在，体力耗尽，则停止
                    print("no more energy for robbing!")
                    break
                judge = self.qiangkuang_judge()
            # if judge==1 or judge==2 or judge==3:
            #     self.click(995,440)   #中间的矿
            #     self.delay(2)
            #     self.qiangkuang_battle(power)
            # if judge==2 or judge==3:
            #     self.click(618,667)   #左下角的矿
            #     self.delay(2)
            #     self.qiangkuang_battle(power)
            if judge == 1 or judge == 2:
                print("Ignore the kuang")
                self.click(int(1738 * self.bili + self.extra_distance), 940)  # 点击重新搜索
                self.delay(2)
            elif judge == 3:
                self.click(int(995 * self.bili + self.extra_distance), 440)  # 中间的矿
                self.delay(2)
                if self.qiangkuang_battle(power) == "OK":
                    continue
                self.click(int(618 * self.bili + self.extra_distance), 667)  # 左下角的矿
                self.delay(2)
                if self.qiangkuang_battle(power) == "OK":
                    continue
                self.click(int(1368 * self.bili + self.extra_distance), 684)  # 右下角的矿
                self.delay(2)
                if self.qiangkuang_battle(power) == "OK":
                    continue
            self.delay(2)

    def get(self):
        if self.check_package() == True:
            bili = self.ratio
        else:
            bili = 1
        self.get_screenshot()
        self.cut_pic((int(957 * self.bili + self.extra_distance), 400),
                     (int(1054 * self.bili + self.extra_distance), 452))

    def get_current_time(self):
        now = datetime.now().strftime("%H")
        print(now)

    def test(self):
        self.get_screenshot()

    def gangsi(self, speed=180):
        start_hight = 160
        while True:
            self.get_screenshot()
            if self.read_word('gangsi_jieshu') == True:
                return False
            gunzi = self.read_word('gangsi_gunzi')
            taozi = self.read_word('gangsi_taozi')
            distance = taozi - gunzi
            time = (distance - start_hight) / speed
            if time > 0:
                print("long press %s seconds" % time)
                time = math.ceil(time * 1000)
                os.system("adb -s %s shell input swipe 1750 970 1750 971 %d" % (self.device_id, time))
                self.delay(2)
            else:
                print("Game end!")
                return False
        print("Game end!")
        # os.system("adb -s %s shell input swipe 1750 970 1750 971 3555" %(self.device_id))

    def lianlian_shibie(self, pic_location=[]):
        '''识别界面上所有小图片并设置成对应的编号'''
        for a in range(5):  # 一次性将所有的图片都识别成对应编号
            for b in range(12):
                x1 = pic_location[a][b][0]
                y1 = pic_location[a][b][1]
                self.lianliankan_getpic(x1, y1, 'original_pic')
                if self.contrast_two_pic('original_pic', 'lianlian_baoyinguai', 'target_pic') == True:
                    pic_location[a][b] = 1
                elif self.contrast_two_pic('original_pic', 'lianlian_bianyinlong', 'target_pic') == True:
                    pic_location[a][b] = 2
                elif self.contrast_two_pic('original_pic', 'lianlian_dajia',
                                           'target_pic') == True or self.contrast_two_pic('original_pic',
                                                                                          'lianlian_dajia2',
                                                                                          'target_pic') == True:
                    pic_location[a][b] = 3
                elif self.contrast_two_pic('original_pic', 'lianlian_dashetou', 'target_pic') == True:
                    pic_location[a][b] = 4
                elif self.contrast_two_pic('original_pic', 'lianlian_dayanshe', 'target_pic') == True:
                    pic_location[a][b] = 5
                elif self.contrast_two_pic('original_pic', 'lianlian_dazhenfeng',
                                           'target_pic') == True or self.contrast_two_pic('original_pic',
                                                                                          'lianlian_dazhenfeng2',
                                                                                          'target_pic') == True:
                    pic_location[a][b] = 6
                elif self.contrast_two_pic('original_pic', 'lianlian_dazuiou', 'target_pic') == True:
                    pic_location[a][b] = 7
                elif self.contrast_two_pic('original_pic', 'lianlian_dazuiwa',
                                           'target_pic') == True or self.contrast_two_pic('original_pic',
                                                                                          'lianlian_dazuiwa2',
                                                                                          'target_pic') == True:
                    pic_location[a][b] = 8
                elif self.contrast_two_pic('original_pic', 'lianlian_shamonaiya',
                                           'target_pic') == True or self.contrast_two_pic('original_pic',
                                                                                          'lianlian_shamonaiya2',
                                                                                          'target_pic') == True:
                    pic_location[a][b] = 9
                elif self.contrast_two_pic('original_pic', 'lianlian_zhichongxiong',
                                           'target_pic') == True or self.contrast_two_pic('original_pic',
                                                                                          'lianlian_zhichongxiong2',
                                                                                          'target_pic') == True:
                    pic_location[a][b] = 10
                else:
                    pic_location[a][b] = 0
        print(pic_location)

    def lianliankan(self):
        self.get_screenshot()
        pic = []  # 存放图片对应编号
        pic_location = []  # 存放图片对应坐标
        for i in range(5):  # 生成一个二维数组
            row = []
            for j in range(12):
                col = []
                x = 301 + j * 120
                y = 349 + i * 121
                col.append(x)
                col.append(y)
                row.append(col)
            pic.append(row)  # 存放图片对应编号
            pic_location.append(row)
        # for k in range(5):  #生成一个二维数组
        #     row=[]
        #     for l in range(12):
        #         col=[]
        #         x=301+j*120
        #         y=349+i*121
        #         col.append(x)
        #         col.append(y)
        #         row.append(col)
        #     pic_location.append(row)  #存放图片对应坐标
        # thread1=threading.Thread(target=self.lianlian_shibie(pic_location))
        _thread.start_new_thread(self.lianlian_shibie, (pic_location,))  # 将图片识别放入线程执行
        # self.lianlian_shibie(pic_location)
        # print pic_location
        total_count = 60
        last_total_count = 60
        while total_count > 0:
            for i in range(5):
                for j in range(12):
                    if pic[i][j] != 0 and isinstance(pic[i][j], int) == True:  # 如果图片还没被消除
                        if i == 0 or i == 4:  # 如果是最上面一排或最下面一排
                            for l in range(j + 1, 12):  # 第一排横向查找
                                if pic[i][l] != 0:  # 如果不为空则比较一下
                                    if pic[i][j] == pic[i][l]:
                                        x1 = 301 + j * 120
                                        y1 = 349 + i * 121
                                        x2 = 301 + l * 120
                                        y2 = 349 + i * 121
                                        # x1=pic_location[i][j][0]
                                        # y1=pic_location[i][j][1]
                                        # x2=pic_location[i][l][0]
                                        # y2=pic_location[i][l][1]
                                        self.click(x1, y1, True)
                                        self.click(x2, y2, True)
                                        # self.click(x2,y2)
                                        print("Heng xiang Xiaochu (%s,%s) (%s,%s)" % (i, j, i, l))
                                        pic[i][j] = 0
                                        pic[i][l] = 0
                                        total_count -= 2
                                        continue
                                elif i == 0:  # 如果是最上面一排已经消除了
                                    # i+=1  #如果上面一格已经消掉了，就向下走一格
                                    down = i + 1
                                    while down < 4:
                                        if pic[down][l] != 0:
                                            break
                                        down = down + 1
                                    if pic[i][j] == pic[down][l]:
                                        x1 = 301 + j * 120
                                        y1 = 349 + i * 121
                                        x2 = 301 + l * 120
                                        y2 = 349 + down * 121
                                        # x1=pic_location[i][j][0]
                                        # y1=pic_location[i][j][1]
                                        # x2=pic_location[i][l][0]
                                        # y2=pic_location[i][l][1]
                                        self.click(x1, y1, True)
                                        self.click(x2, y2, True)
                                        print("Di 1 lie Xiaochu (%s,%s) (%s,%s)" % (i, j, down, l))
                                        pic[i][j] = 0
                                        pic[down][l] = 0
                                        total_count -= 2
                                        continue
                                elif i == 4:  # 如果是最上面一排已经消除了
                                    # i+=1  #如果上面一格已经消掉了，就向下走一格
                                    up = i - 1
                                    while up > 0:
                                        if pic[up][l] != 0:
                                            break
                                        up = up - 1
                                    if pic[i][j] == pic[up][l]:
                                        x1 = 301 + j * 120
                                        y1 = 349 + i * 121
                                        x2 = 301 + l * 120
                                        y2 = 349 + up * 121
                                        # x1=pic_location[i][j][0]
                                        # y1=pic_location[i][j][1]
                                        # x2=pic_location[i][l][0]
                                        # y2=pic_location[i][l][1]
                                        self.click(x1, y1, True)
                                        self.click(x2, y2, True)
                                        print("Di 5 lie Xiaochu (%s,%s) (%s,%s)" % (i, j, up, l))
                                        pic[i][j] = 0
                                        pic[up][l] = 0
                                        total_count -= 2
                                        continue
                        elif j < 11 and pic[i][j] != 0:  # 如果不是上下两端，就向右查找
                            l = j + 1
                            while l < 11:
                                if pic[i][l] != 0:
                                    break
                                l = l + 1
                            if pic[i][j] == pic[i][l]:
                                x1 = 301 + j * 120
                                y1 = 349 + i * 121
                                x2 = 301 + l * 120
                                y2 = 349 + i * 121
                                # x1=pic_location[i][j][0]
                                # y1=pic_location[i][j][1]
                                # x2=pic_location[i][l][0]
                                # y2=pic_location[i][l][1]
                                self.click(x1, y1, True)
                                self.click(x2, y2, True)
                                print("Di 2~4 lie heng  xiang Xiaochu (%s,%s) (%s,%s)" % (i, j, i, l))
                                pic[i][j] = 0
                                pic[i][l] = 0
                                total_count -= 2
                                continue
                            elif l > j + 1:  # 如果不是紧贴的右边一格，顺便查找路径上的上下两端的匹配项
                                for right in range(j + 1, l):
                                    up = i - 1
                                    while up > 0:
                                        if pic[up][right] != 0:
                                            break
                                        up = up - 1
                                    if pic[i][j] == pic[up][right]:
                                        x1 = 301 + j * 120
                                        y1 = 349 + i * 121
                                        x2 = 301 + right * 120
                                        y2 = 349 + up * 121
                                        self.click(x1, y1, True)
                                        self.click(x2, y2, True)
                                        print("Di 2~4 lie you shang Xiaochu (%s,%s) (%s,%s)" % (i, j, up, right))
                                        pic[i][j] = 0
                                        pic[up][right] = 0
                                        total_count -= 2
                                        continue
                                    down = i + 1
                                    while down < 4:
                                        if pic[down][right] != 0:
                                            break
                                        down = down + 1
                                    if pic[i][j] == pic[down][right]:
                                        x1 = 301 + j * 120
                                        y1 = 349 + i * 121
                                        x2 = 301 + right * 120
                                        y2 = 349 + down * 121
                                        self.click(x1, y1, True)
                                        self.click(x2, y2, True)
                                        print("Di 2~4 lie you xia Xiaochu (%s,%s) (%s,%s)" % (i, j, down, right))
                                        pic[i][j] = 0
                                        pic[down][right] = 0
                                        total_count -= 2
                                        continue
                        if i < 4 and pic[i][j] != 0:  # 如果还是没找到，向下查找
                            k = i + 1
                            while k < 4:
                                if pic[k][j] != 0:
                                    break
                                k = k + 1
                            if pic[i][j] == pic[k][j]:
                                x1 = 301 + j * 120
                                y1 = 349 + i * 121
                                x2 = 301 + j * 120
                                y2 = 349 + k * 121
                                # x1=pic_location[i][j][0]
                                # y1=pic_location[i][j][1]
                                # x2=pic_location[k][j][0]
                                # y2=pic_location[k][j][1]
                                self.click(x1, y1, True)
                                self.click(x2, y2, True)
                                print("Xiang xia Xiaochu (%s,%s) (%s,%s)" % (i, j, k, j))
                                pic[i][j] = 0
                                pic[k][j] = 0
                                total_count -= 2
                                continue
                            elif k > i + 1 and j < 11:  # 如果不是紧贴的下面一格，顺便查找路径上的右侧的匹配项,(左侧的已经通过向右检测验证过了)
                                for down in range(i + 1, k):
                                    right = j + 1
                                    while right < 11:
                                        if pic[down][right] != 0:
                                            break
                                        right = right + 1
                                    if pic[i][j] == pic[down][right]:
                                        x1 = 301 + j * 120
                                        y1 = 349 + i * 121
                                        x2 = 301 + right * 120
                                        y2 = 349 + down * 121
                                        self.click(x1, y1, True)
                                        self.click(x2, y2, True)
                                        print("Xiang xia you ce Xiaochu (%s,%s) (%s,%s)" % (i, j, down, right))
                                        pic[i][j] = 0
                                        pic[down][right] = 0
                                        total_count -= 2
                                        continue
                                    elif right > j + 1:  # 向右查探的路径上，上下两面也可以消除
                                        for forward in range(j + 1, right):
                                            goup = i
                                            while goup > 0:
                                                if pic[i][j] == pic[goup][forward]:
                                                    break
                                                goup = goup - 1
                                            if pic[i][j] == pic[goup][forward]:
                                                x1 = 301 + j * 120
                                                y1 = 349 + i * 121
                                                x2 = 301 + forward * 120
                                                y2 = 349 + goup * 121
                                                self.click(x1, y1, True)
                                                self.click(x2, y2, True)
                                                print(
                                                    "Xiang xia you de shang xia liang mian Xiaochu (%s,%s) (%s,%s)" % (
                                                    i, j, goup, forward))
                                                pic[i][j] = 0
                                                pic[goup][forward] = 0
                                                total_count -= 2
                                                continue
                        elif i > 0 and pic[i][j] != 0 and j < 11:  # 向上右侧查找
                            top = i - 1
                            while top > 0:
                                if pic[top][j] != 0:
                                    break
                                top = top - 1
                            if top < i - 1:  # 如果上方有消除的块
                                for up in range(top, i):
                                    right = j + 1
                                    while right < 11:
                                        if pic[up][right] != 0:
                                            break
                                        right = right + 1
                                    if pic[i][j] == pic[up][right]:
                                        x1 = 301 + j * 120
                                        y1 = 349 + i * 121
                                        x2 = 301 + right * 120
                                        y2 = 349 + up * 121
                                        self.click(x1, y1, True)
                                        self.click(x2, y2, True)
                                        print("Xiang shang you Xiaochu (%s,%s) (%s,%s)" % (i, j, up, right))
                                        pic[i][j] = 0
                                        pic[up][right] = 0
                                        total_count -= 2
                                        continue
                                if top == 0 and pic[0][j] == 0:  # 消除块上面的块都已经被消除了，那就变成了顶端块
                                    start = 0
                                    right = j + 1
                                    for go in range(right, 11):
                                        while start < 4:
                                            if pic[start][go] != 0:
                                                break
                                            start = start + 1
                                        if pic[i][j] == pic[start][go]:
                                            x1 = 301 + j * 120
                                            y1 = 349 + i * 121
                                            x2 = 301 + go * 120
                                            y2 = 349 + start * 121
                                            self.click(x1, y1, True)
                                            self.click(x2, y2, True)
                                            print("Dang zuo ding duan Xiaochu (%s,%s) (%s,%s)" % (i, j, start, go))
                                            pic[i][j] = 0
                                            pic[start][go] = 0
                                            total_count -= 2
                                            continue
                    else:
                        continue
            if last_total_count > total_count + 2:  # 这一轮消除掉超过一对
                print("Currently leave %s pictures, rescan!" % total_count)
            elif total_count < 40 and last_total_count != total_count:  # 或者当前已经消除掉10对以上
                self.click(817, 1020, True)  # 点击重新排序的按钮
                print("Click replace button")
                self.delay(1)
                self.get_screenshot()
                pic_location_new = []  # 存放图片对应坐标
                for i in range(5):  # 生成一个二维数组
                    row = []
                    for j in range(12):
                        col = []
                        x = 301 + j * 120
                        y = 349 + i * 121
                        col.append(x)
                        col.append(y)
                        row.append(col)
                    pic_location_new.append(row)
                _thread.start_new_thread(self.lianlian_shibie, (pic_location_new,))  # 将图片识别放入线程执行
            last_total_count = total_count
            i = 0
            j = 0

    def lianliankan_getpic(self, x=0, y=0, name=''):
        self.cut_pic((x - 30, y - 30), (x + 30, y + 30), False, name)

    def gongdian(self):
        for i in range(20):
            print("The floor of num: %s" % (i + 1))
            self.click(1250, 870)  # 随便在界面上点一下保证触发方向按键
            os.system("adb -s %s shell input swipe 650 670 650 670 3000" % (self.device_id))
            self.click(1970, 880)  # 点击对话
            self.delay(1)
            self.click(1250, 870)
            self.delay(1)
            self.click(1250, 870)
            self.delay(2)
            self.click(1580, 420)  # 点击挑战
            print("Wait 15 seconds for battling")
            self.delay(15)  # 等待15秒战斗
            self.click(1250, 870)
            self.delay(1)
            self.click(1430, 890)  # 点击确认奖励
            self.delay(2)
            self.click(1250, 870)  # 随便在界面上点一下保证触发方向按键
            self.click(760, 810)  # 往右走绕开
            os.system("adb -s %s shell input swipe 760 810 760 810 200" % (self.device_id))
            self.delay(1)
            os.system("adb -s %s shell input swipe 650 670 650 670 200" % (self.device_id))  # 往前走
            self.click(520, 810)  # 往左走回来
            os.system("adb -s %s shell input swipe 520 810 520 810 200" % (self.device_id))
            self.delay(1)
            self.click(650, 670)  # 往前进入下一层
            os.system("adb -s %s shell input swipe 650 670 650 670 3000" % (self.device_id))
            self.delay(4)
            print("Into next floor...")

    def select_device(self):
        string = subprocess.Popen('adb devices', shell=True, stdout=subprocess.PIPE)
        totalstring = string.stdout.read()
        totalstring = totalstring.decode('utf-8')
        # print(totalstring)
        devicelist = re.compile(r'(\w*)\s*device\b').findall(totalstring)
        devicenum = len(devicelist)
        if devicenum == 0:
            print("Currently have no connected devices!")
            return False
        elif devicenum == 1:
            print("Currently have one connected device:%s." % devicelist[0])
            return devicelist[0]
        else:
            print("Currently have more than one connected devices! input the number to choose the device:")
            dictdevice = {}
            for i in range(devicenum):
                string = subprocess.Popen("adb -s %s shell getprop ro.product.device" % devicelist[i], shell=True,
                                          stdout=subprocess.PIPE)
                modestring = string.stdout.read().strip()  # 去除掉自动生成的回车
                battery_level = self.get_ballery_level(devicelist[i])
                print("%s:%s---%s     battery_level: %s" % (i + 1, devicelist[i], modestring, battery_level))
                dictdevice[i + 1] = devicelist[i]
            num = input()
            num = int(num)
            while not num in dictdevice.keys():
                print('Pls input the right num again!')
                num = input()
                num = int(num)
            return dictdevice[num]

    def get_ballery_level(self, deviceid=''):
        battery_info = subprocess.Popen("adb -s %s shell dumpsys battery" % deviceid, shell=True,
                                        stdout=subprocess.PIPE)
        battery_info_string = battery_info.stdout.read()
        battery_info_string = bytes.decode(battery_info_string)
        location = re.search('level:', battery_info_string)
        span = location.span()
        start, end = span
        start = end + 1
        for i in range(5):
            end += 1
            if battery_info_string[end] == "\n":
                break
        battery_level = battery_info_string[start:end]  # 第几个到第几个中间接冒号
        return battery_level

    def start_play(self):
        self.device_id = self.select_device()
        string = subprocess.Popen("adb -s %s shell getprop ro.product.model" % self.device_id, shell=True,
                                  stdout=subprocess.PIPE)
        self.device_model = string.stdout.read().strip()  # 去除掉自动生成的回车
        self.device_model = self.device_model.decode('utf-8')
        # print("Input the num to choose device type:\n 1 T1 \n 2 NOT T1"
        # dev=input()
        if "T7" in self.device_model or "T8" in self.device_model:
            print("It's a T1 family device.")
            self.bili = 1
            self.extra_distance = self.distance
            # self.check_package(self.device_id)
        else:
            self.extra_distance = self.distance
        print("Input the num to select function! \n" \
              "1 auto PVP\n" \
              "2 auto 5 diamond battle\n" \
              "3 auto qiang kuang\n" \
              "4 auto Youxiwang Boss\n" \
              "5 auto geti\n")
        num = input()
        if num == '1':
            self.duizhan_battle(self.device_id)
        elif num == '2':
            self.tiaozhan()
        elif num == '3':
            self.qiangkuang(300000)
        elif num == '4':
            self.shuizhu()
        elif num == '5':
            self.geti()


if __name__ == '__main__':
    test = fuke('')  # c85df50c 1163746998
    test.start_play()
