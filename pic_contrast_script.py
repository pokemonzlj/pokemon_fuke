#-*-coding:utf-8-*-

from __future__ import division
import os
import sys
import math
import operator
from PIL import Image
import time
from datetime import datetime
from PIL import ImageGrab

class contrast_pic:
    def __init__(self, device):
        self.device_id=device

    def get_screenshot(self,path='pic'):
        if path=='pic':
            path = os.path.dirname(__file__)+'/pic'
        else:
            path = os.path.dirname(__file__)+'/target_pic'
        os.system('adb  -s %s shell screencap -p /sdcard/DCIM/screenshot.png' %self.device_id)   #-p: save the file as a png
        os.system('adb  -s %s pull /sdcard/DCIM/screenshot.png %s ' %(self.device_id,path) )


    def cut_pic(self, left_up=(0,63), right_down=(1080,1620),target=False, path_target=os.path.dirname(__file__)+'/target_pic', resolution=(1080,1620)):
        '''(0,63)正好可以裁剪掉状态栏�'''
        if target==False:
            path = os.path.dirname(__file__)+'/pic'
            pic1_path=path+'/screenshot.png'
            pic=Image.open(pic1_path)
            cut_pic_path=path+'/cut.png'
            pic.crop((left_up[0],left_up[1],right_down[0],right_down[1])).save(cut_pic_path)
        else:
            path=path_target
            pic=Image.open(path)
            cut_pic_path=os.path.dirname(__file__)+'/pic/cut_target.png'
            pic.crop((left_up[0],left_up[1],right_down[0],right_down[1])).save(cut_pic_path)


    def switch_pic(self, cut=False, color=False):
        path = os.path.dirname(__file__)+'/pic'
        if cut==False:
            pic1_path=path+'/screenshot.png'
        else:
            pic1_path=path+'/cut.png'
        pic=Image.open(pic1_path)
        if color==False:
            pic=pic.convert('1').save(pic1_path)

    def contrast_black_pic(self,target_pic='1'):
        path = os.path.dirname(__file__)+'/pic/cut.png'
        path_target=os.path.dirname(__file__)+'/target_pic/%s.png' %target_pic
        path_edited=os.path.dirname(__file__)+'/pic/cut_edited.png'
        path_target_edited=os.path.dirname(__file__)+'/pic/cut_parget_edited.png'
        pic=Image.open(path)
        pic=pic.convert('L')
        # pix_pic=pic.load()
        pic.save(path_edited)
        pic_target=Image.open(path_target)
        pic_target=pic_target.convert('L')
        pic_target.save(path_target_edited)
        # pix_target=pic_target.load()
        same=0
        total=0
        for x in range(pic.size[0]):
            for y in range(pic.size[1]):
                #if pix_pic[x,y]==pix_target[x,y]:
                if -4<=pic.getpixel((x,y))-pic_target.getpixel((x,y))<=4:
                    same+=1
                total+=1
        #print same/total
        if same/total>0.7:
            #print 'same target pic!'
            return True
        else:
            #print 'pic can not match the target one!'
            return  False

    def contrast_pic(self, target_pic='1', cut=False, left_up=(0,63), right_down=(1080,1620)):
        path = os.path.dirname(__file__)+'/pic'
        path_target=os.path.dirname(__file__)+'/target_pic/%s.png' %target_pic
        path_target_cut=os.path.dirname(__file__)+'/pic/cut_target.png'
        pic1_path=path+'/cut.png'
        if cut==False:
            #pic1_path=path+'/screenshot.png'
            self.cut_pic()
            self.cut_pic(target=True,path_target=path_target)
        else:
            #pic1_path=path+'/cut.png'
            self.cut_pic(left_up,right_down)
            self.cut_pic(left_up,right_down,True,path_target)
        pic=Image.open(pic1_path)
        pic=pic.convert('1')
        pic_target=Image.open(path_target_cut)
        pic_target=pic_target.convert('1')
        pic_histogram=pic.histogram()
        pic_target_histogram=pic_target.histogram()
        differ = math.sqrt(reduce(operator.add, list(map(lambda a,b: (a-b)**2,pic_histogram, pic_target_histogram)))/len(pic_histogram))
        #print differ
        if differ<20:
            print "pic match, pass!"
            return True
        else:
            print "Current pic is diferent from target pic!"
            time=datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
            os.rename(pic1_path,path+'/cut_%s.png' %time)
            os.rename(path_target_cut,path+'/cut_target_%s.png'%time)
            print "The time is %s" %time
            return False

    def click(self,x=0,y=0):
        os.system("adb -s %s shell input tap %s %s"  %(self.device_id,x,y))

    def input(self,word=''):
        os.system("adb -s %s shell input text %s" %(self.device_id,word))

    def swipe(self,direction='up'):
        direction=direction.lower()
        if direction=='up':
            os.system("adb -s %s shell input swipe 700 1300 700 500 2000" %self.device_id)
        elif direction=='down':
            os.system("adb -s %s shell input swipe 700 500 700 1300 2000" %self.device_id)
        elif direction=='left':
            os.system("adb -s %s shell input swipe 580 620 880 620 2000" %self.device_id)
        elif direction=='right':
            os.system("adb -s %s shell input swipe 580 620 880 620 2000" %self.device_id)
        elif direction=='button':
            os.system("adb -s %s shell input swipe 700 1300 700 500 100" %self.device_id)
        elif direction=='top':
            os.system("adb -s %s shell input swipe 700 500 700 1300 100" %self.device_id)
        else:
            print "Wrong direction"

    def open_notification_bar(self):
        os.system("adb -s %s shell input swipe 500 0 500 700 500" %self.device_id)
        time.sleep(1)

    def open_quick_settings_bar(self):
        self.open_notification_bar()
        os.system("adb -s %s shell input swipe 500 0 500 700 500" %self.device_id)
        time.sleep(1)

    def home(self):
        os.system("adb -s %s shell input keyevent 3"  %self.device_id)

    def back(self):
        os.system("adb -s %s shell input keyevent 4"  %self.device_id)

    def recent(self):
        os.system("adb -s %s shell input keyevent 20"  %self.device_id)

    def delay(self,detime=1):
        time.sleep(detime)


if __name__ == '__main__':
    test=contrast_pic('5000003470')
    # test.contrast_pic(2)
    test.swipe('up')
    test.get_screenshot()
    test.contrast_pic('4')