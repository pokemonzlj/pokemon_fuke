#-*-coding:utf-8-*-

from __future__ import division
import os
import sys
from PIL import Image
import pytesseract
import time
import winsound  #win声音
from datetime import datetime
from PIL import ImageGrab

def get_pic(id='6EB0217A17002609'):
    path = os.path.dirname(__file__)+'/pic'
    os.system('adb  -s %s shell screencap -p /sdcard/DCIM/roll.png' %id)   #-p: save the file as a png
    os.system('adb  -s %s pull /sdcard/DCIM/roll.png %s ' %(id,path) )

def cut_pic(weizhi='attend_one'):
    path=os.path.dirname(__file__)+'/pic'
    pic_need_cut=path+'/roll.png'
    pic=Image.open(pic_need_cut)
    cut_pic_path=path+'/cut.png'
    value_pic_path=path+'/value.png'
    if weizhi=='attend_one':
        pic.crop((15,1012,90,1078)).save(cut_pic_path)  #第1个已参加的已字的位置
    elif weizhi=='attend_two':
        pic.crop((15,1581,90,1647)).save(cut_pic_path)  #第2个已参加已字的位置
    elif weizhi=='attend_three':
        pic.crop((15,2150,90,2216)).save(cut_pic_path)  #第3个已参加已字的位置
    elif weizhi=='code':
        pic.crop((810,1170,1110,1290)).save(cut_pic_path)  #显示验证码的位置
    elif weizhi=='value_one':
        pic.crop((1292,801,1400,877)).save(value_pic_path)
    elif weizhi=='value_two':
        pic.crop((1292,1370,1400,1446)).save(value_pic_path)
    elif weizhi=='value_three':
        pic.crop((1292,1939,1400,2015)).save(value_pic_path)
    elif weizhi=='attend':
        pic.crop((595,875,840,1180)).save(cut_pic_path)  #参加活动的大框的中间一部分（为了应对异常的过长的介绍说明，多往下截一点图）

def analyse_pic(weizhi='one'):
    path = os.path.dirname(__file__)+'/pic'
    cut_pic_path=path+'/cut.png'
    value_pic_path=path+'/value.png'
    verification_code=path+'/verification_code.png'
    # pic_new=pic_new.convert('L')  #转化为灰度图像
    # pic_new=pic_new.convert('1')  #convert方法可以将图片转成黑白
    if weizhi=='attend_one' or weizhi=='attend_two' or weizhi=='attend_three':
        pic_new=Image.open(cut_pic_path)
        pic_new=pic_new.convert('RGBA')
        pix=pic_new.load()
        for y in range(pic_new.size[1]):  # 二值化处理，这个阈值为R=95，G=95，B=95
            for x in range(pic_new.size[0]):
                if pix[x, y][0] == 255 and 148 < pix[x, y][1] < 156 and 35 < pix[x, y][2] < 42:
                    return 'no'
        return 'yes'  #当没有识别到已参加，就返回yes
    elif weizhi=='value_one' or weizhi=='value_two' or weizhi=='value_three':
        pic_new=Image.open(value_pic_path)
        pic_new=pic_new.convert('RGBA')
        g=pic_new.histogram()
        pic_sample=Image.open(os.path.dirname(__file__)+'/value_sample.png')
        pic_sample=pic_sample.convert('RGBA')
        f=pic_sample.histogram()   #转化成直方图
        data=[]
        for index in range(0,len(g)):
            if g[index] != f[index]:
                data.append(1-abs(g[index]-f[index])/max(g[index],f[index]))
            else:
                data.append(1)
        if (sum(data)/len(g)) <= 0.92:   #实测0.02的时候匹配度是0.88左右
            #print "the histogram rate value is :%s <= 0.92" %(sum(data)/len(g))
            return 'yes' #当不是0.01的时候返回yes
        else:
            print "find value is 0.01, ignore it."
            #print "the histogram rate value is :%s > 0.92" %(sum(data)/len(g))
            return 'no'
    elif weizhi=='code':
        pic_new=Image.open(cut_pic_path)
        pic_new=pic_new.convert('RGBA')
        pix=pic_new.load()
        #word=pytesseract.image_to_string(pic_new)
        for y in range(pic_new.size[1]):  # 二值化处理，这个阈值为R=95，G=95，B=95
            for x in range(pic_new.size[0]):   #size[0]即图片长度，size[1]即图片高度
                if pix[x, y][0] < 92 or pix[x, y][1] < 94 or pix[x, y][2] < 92:
                    pix[x, y] = (0, 0, 0, 255)   #黑色
                else:
                    pix[x, y] = (255, 255, 255, 255)  #白色
        pic_new.save(verification_code)
        return True
    elif weizhi=='attend':
        pic_new=Image.open(cut_pic_path)
        pic_new=pic_new.convert('RGBA')
        pix=pic_new.load()
        for y in range(pic_new.size[1]):  # 二值化处理，这个阈值为R=95，G=95，B=95
            for x in range(pic_new.size[0]):
                if pix[x, y][0] == 255 and 148 < pix[x, y][1] < 156 and 35 < pix[x, y][2] < 42:
                    if y < (pic_new.size[1])/3:  #在总长度1/3以上找到则是正常情况
                        return 'up'
                    else:
                        return 'down'
        return False

def cut_and_analyse_pic(weizhi='attend_one'):
    cut_pic(weizhi)
    return analyse_pic(weizhi)

def update_page(id='6EB0217A17002609'):
    os.system("adb -s %s shell input swipe 400 500 400 1000 100"  %id)  #下拉刷新
    time.sleep(3)


def auto_update(id='6EB0217A17002609'):
    for i in range(10000):
        update_page(id)
        get_pic(id)
        if cut_and_analyse_pic('attend_one')=='yes' and cut_and_analyse_pic('value_one')=='yes':
            os.system("adb -s %s shell input tap 120 1048" %id)  #第一条roll的内容
            print 'find unchecked in place one and value > 0.01'
        elif cut_and_analyse_pic('attend_two')=='yes' and cut_and_analyse_pic('value_two')=='yes':
            os.system("adb -s %s shell input tap 120 1617" %id)
            print 'find unchecked in place two and value > 0.01'
        elif cut_and_analyse_pic('attend_three')=='yes' and cut_and_analyse_pic('value_three')=='yes':
            os.system("adb -s %s shell input tap 120 2183" %id)
            print 'find unchecked in place three and value > 0.01'
        else:
            time.sleep(100)
            continue
        time.sleep(2)
        os.system("adb -s %s shell input tap 720 960" %id)  #点击参加
        time.sleep(1)
        get_pic(id)
        cut_and_analyse_pic('code')
        winsound.Beep(600,1000)
        os.system("adb -s %s shell input tap 490 1230" %id)  #点击输入框
        time.sleep(98)

def auto_update_easy(id='6EB0217A17002609'):
    '''用于最简单的判断，判断成功则提醒，不会进入界面'''
    for i in range(10000):
        update_page(id)
        time.sleep(10)
        get_pic(id)
        if cut_and_analyse_pic('attend_one')=='yes' and cut_and_analyse_pic('value_one')=='yes':
            print 'find unchecked in place one and value > 0.01'
        elif cut_and_analyse_pic('attend_two')=='yes' and cut_and_analyse_pic('value_two')=='yes':
            print 'find unchecked in place two and value > 0.01'
        elif cut_and_analyse_pic('attend_three')=='yes' and cut_and_analyse_pic('value_three')=='yes':
            print 'find unchecked in place three and value > 0.01'
        else:
            time.sleep(70)
            continue
        winsound.Beep(600,1000)
        time.sleep(30)  #当能找到的时候，短时间内再刷一次



def auto_update_manual(id='6EB0217A17002609'):
    '''用于脱离手机，直接在电脑上看验证码并输入，直接完成输入的操作'''
    for i in range(10000):
        update_page(id)
        time.sleep(5)  #网络延迟的时候加延迟
        get_pic(id)
        if cut_and_analyse_pic('attend_one')=='yes' and cut_and_analyse_pic('value_one')=='yes':
            os.system("adb -s %s shell input tap 120 1048" %id)  #第一条roll的内容
            print 'find unchecked in place one and value > 0.01'
        elif cut_and_analyse_pic('attend_two')=='yes' and cut_and_analyse_pic('value_two')=='yes':
            os.system("adb -s %s shell input tap 120 1617" %id)
            print 'find unchecked in place two and value > 0.01'
        elif cut_and_analyse_pic('attend_three')=='yes' and cut_and_analyse_pic('value_three')=='yes':
            os.system("adb -s %s shell input tap 120 2183" %id)
            print 'find unchecked in place three and value > 0.01'
        else:
            time.sleep(95)
            continue
        time.sleep(2)
        while True:
            get_pic(id)
            result=analyse_pic('attend')
            if result=='up':
                os.system("adb -s %s shell input tap 720 960" %id)  #点击参加
            elif result=='down':
                os.system("adb -s %s shell input tap 720 1060" %id)  #点击参加
            time.sleep(1)
            get_pic(id)
            analyse_pic('code')
            winsound.Beep(600,1000)
            #os.system("adb -s %s shell input tap 490 1230" %id)  #点击输入框
            code=raw_input("Input verification code: ")
            os.system("adb -s %s shell input tap 480 1210" %id)   #点击一下输入框的位置
            time.sleep(1)
            os.system("adb -s %s shell input text %s" %(id,code))   #输入验证码
            time.sleep(1)
            os.system("adb -s %s shell input tap 480 970" %id)   #点击确定
            time.sleep(2)
            os.system("adb -s %s shell input tap 740 730" %id)   #无论是否存在输入成功确认框，都点击一下文字介绍的位置关闭确认框
            get_pic(id)
            if analyse_pic('attend')==False:
                print "input verification code succeed."
                #os.system("adb -s %s shell input keyevent 4" %id)  #按返回键退出确认框
                os.system("adb -s %s shell input tap 60 180" %id)   #点击回退,返回整个的roll列表
                break
            print "input verification code failed,try again."

if __name__ == '__main__':
   #update_page('6EB0217A17002609')
   #get_pic()
   auto_update_easy()
   #auto_update()
   #auto_update_manual()
   #read_word('middle')