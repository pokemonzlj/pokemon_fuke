#-*-coding:utf-8-*-
"""ADB设备基础操作模块"""
from __future__ import division
import os
import sys
import math
import operator
from functools import reduce
from PIL import Image
import time
import subprocess
from datetime import datetime

class ADBDevice:
    """ADB设备基础操作类"""
    
    def __init__(self, device_id):
        self.device_id = device_id

    def _compare_histogram(self, pic1, pic2):
        """比较两张图片的直方图差异"""
        hist1 = pic1.histogram()
        hist2 = pic2.histogram()
        return math.sqrt(reduce(operator.add, list(map(lambda a,b: (a-b)**2, hist1, hist2)))/len(hist1))

    def get_screenshot(self, path='pic'):
        """获取设备截图"""
        if path == 'pic':
            path = os.path.dirname(__file__) + '/pic'
        else:
            path = os.path.dirname(__file__) + '/target_pic'
        subprocess.Popen(
            'adb -s %s shell screencap -p /sdcard/DCIM/screenshot.png' % self.device_id).wait()
        subprocess.Popen(
            'adb -s %s pull /sdcard/DCIM/screenshot.png %s ' % (self.device_id, path),
            stdout=subprocess.PIPE).wait()
        print("Get current screenshot")
        subprocess.Popen('adb -s %s shell rm /sdcard/DCIM/screenshot.png' % self.device_id).wait()

    def get_pic(self):
        """获取带时间戳的设备截图（用于保存奖励等场景）"""
        path = os.path.dirname(__file__) + '/pic'
        timepic = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        subprocess.Popen(
            'adb -s %s shell screencap -p /sdcard/DCIM/screenshot.png' % self.device_id).wait()
        subprocess.Popen(
            'adb -s %s pull /sdcard/DCIM/screenshot.png %s/%s.png ' % (self.device_id, path, timepic),
            stdout=subprocess.PIPE).wait()
        print("Get reward screenshot")
        subprocess.Popen('adb -s %s shell rm /sdcard/DCIM/screenshot.png' % self.device_id).wait()

    def cut_pic(self, left_up=(0, 63), right_down=(1080, 1620), target='', name='', resolution=(1080, 2400)):
        """裁剪截图，获取需要的小图片方便识别
        - target: 目标截图文件夹路径，为空则从pic/screenshot.png裁剪
        - name: 保存的文件名，为空则保存为cut.png
        """
        if target == '' or target == False:
            path = os.path.dirname(__file__) + '/pic'
            pic1_path = path + '/screenshot.png'
            pic = Image.open(pic1_path)
            if name == '':
                cut_pic_path = path + '/cut.png'
            else:
                cut_pic_path = path + '/' + name + '.png'
            pic.crop((left_up[0], left_up[1], right_down[0], right_down[1])).save(cut_pic_path)
            return True
        path_target = os.path.dirname(__file__) + '/pic/' + target
        pic1_path = path_target + '/screenshot.png'
        pic = Image.open(pic1_path)
        if name == '':
            cut_pic_path = path_target + '/cut.png'
        else:
            cut_pic_path = path_target + '/' + name + '.png'
        pic.crop((left_up[0], left_up[1], right_down[0], right_down[1])).save(cut_pic_path)

    def switch_pic(self, cut=False, color=False):
        """转换图片格式"""
        path = os.path.dirname(__file__) + '/pic'
        if cut == False:
            pic1_path = path + '/screenshot.png'
        else:
            pic1_path = path + '/cut.png'
        pic = Image.open(pic1_path)
        if color == False:
            pic = pic.convert('1')
            pic.save(pic1_path)

    def contrast_two_pic(self, name1='', name2='', albumname='pic'):
        """比较两张图片"""
        path_original = os.path.dirname(__file__) + '/pic/' + name1 + '.png'
        if albumname == 'pic':
            path_contrast = os.path.dirname(__file__) + '/pic/' + name2 + '.png'
        elif albumname == 'target_pic':
            path_contrast = os.path.dirname(__file__) + '/target_pic/' + name2 + '.png'
        pic_original = Image.open(path_original)
        pic_original = pic_original.convert('1')
        pic_contrast = Image.open(path_contrast)
        pic_contrast = pic_contrast.convert('1')
        differ = self._compare_histogram(pic_original, pic_contrast)
        if differ < 1.5:
            return True
        else:
            return False

    def contrast_grey_pic(self, target_pic='1'):
        """灰度图片对比"""
        path = os.path.dirname(__file__) + '/pic/cut.png'
        path_target = os.path.dirname(__file__) + '/target_pic/%s.png' % target_pic
        path_edited = os.path.dirname(__file__) + '/pic/cut_edited.png'
        path_target_edited = os.path.dirname(__file__) + '/pic/cut_parget_edited.png'
        pic = Image.open(path)
        pic = pic.convert('L')
        pic.save(path_edited)
        pic_target = Image.open(path_target)
        pic_target = pic_target.convert('L')
        pic_target.save(path_target_edited)
        same = 0
        total = 0
        for x in range(pic.size[0]):
            for y in range(pic.size[1]):
                if -4 <= pic.getpixel((x, y)) - pic_target.getpixel((x, y)) <= 4:
                    same += 1
                total += 1
        print("The two grey pics match rate is %s" % (same / total))
        if same / total > 0.7:
            return True
        else:
            return False

    def contrast_pic(self, target_pic='1', cut=False, left_up=(0, 63), right_down=(1080, 1620)):
        """对比目标图片"""
        path = os.path.dirname(__file__) + '/pic'
        path_target = os.path.dirname(__file__) + '/target_pic/%s.png' % target_pic
        path_target_cut = os.path.dirname(__file__) + '/pic/cut_target.png'
        pic1_path = path + '/cut.png'
        if cut == False:
            self.cut_pic()
            self.cut_pic(target=True, path_target=path_target)
        else:
            self.cut_pic(left_up, right_down)
            self.cut_pic(left_up, right_down, True, path_target)
        pic = Image.open(pic1_path)
        pic = pic.convert('1')
        pic_target = Image.open(path_target_cut)
        pic_target = pic_target.convert('1')
        differ = self._compare_histogram(pic, pic_target)
        if differ < 20:
            print("pic match, pass!")
            return True
        else:
            print("Current pic is diferent from target pic!")
            timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
            os.rename(pic1_path, path + '/cut_%s.png' % timestamp)
            os.rename(path_target_cut, path + '/cut_target_%s.png' % timestamp)
            print("The time is %s" % timestamp)
            return False

    def click(self, x=0, y=0, issubprocess=False):
        """点击指定坐标"""
        if issubprocess == False:
            os.system("adb -s %s shell input tap %s %s" % (self.device_id, x, y))
        elif issubprocess == True:
            subprocess.call("adb -s %s shell input tap %s %s" % (self.device_id, x, y), shell=True)

    def input(self, word=''):
        """输入文本"""
        os.system("adb -s %s shell input text %s" % (self.device_id, word))

    def swipe(self, direction='up'):
        """滑动屏幕，支持方向：up/down/left/right/button/top"""
        direction = direction.lower().strip()
        if direction == 'up':
            os.system("adb -s %s shell input swipe 700 1300 700 500 2000" % self.device_id)
        elif direction == 'down':
            os.system("adb -s %s shell input swipe 700 500 700 1300 2000" % self.device_id)
        elif direction == 'left':
            os.system("adb -s %s shell input swipe 880 620 580 620 2000" % self.device_id)
        elif direction == 'right':
            os.system("adb -s %s shell input swipe 580 620 880 620 2000" % self.device_id)
        elif direction == 'button':
            os.system("adb -s %s shell input swipe 700 1300 700 500 100" % self.device_id)
        elif direction == 'top':
            os.system("adb -s %s shell input swipe 700 500 700 1300 100" % self.device_id)
        else:
            print("Wrong direction")

    def swipe_custom(self, x1, y1, x2, y2, steps=200):
        """自定义滑动，从(x1,y1)滑动到(x2,y2)"""
        os.system("adb -s %s shell input swipe %s %s %s %s %s" % 
                   (self.device_id, x1, y1, x2, y2, steps))

    def open_notification_bar(self):
        """打开通知栏"""
        os.system("adb -s %s shell input swipe 500 0 500 700 500" % self.device_id)
        time.sleep(1)

    def open_quick_settings_bar(self):
        """打开快捷设置栏"""
        os.system("adb -s %s shell input swipe 500 0 500 700 500" % self.device_id)
        time.sleep(0.5)
        os.system("adb -s %s shell input swipe 500 0 500 700 500" % self.device_id)
        time.sleep(1)

    def home(self):
        """按Home键"""
        os.system("adb -s %s shell input keyevent 3" % self.device_id)

    def back(self):
        """按返回键"""
        os.system("adb -s %s shell input keyevent 4" % self.device_id)

    def recent(self):
        """按最近任务键"""
        os.system("adb -s %s shell input keyevent 20" % self.device_id)

    def delay(self, seconds=1):
        """延时"""
        time.sleep(seconds)


if __name__ == '__main__':
    test = ADBDevice('5000003470')