# -*-coding:utf-8-*-
import os
import sys
from PIL import Image
import time
import threading
import _thread
from datetime import datetime
from PIL import ImageGrab, Image
from adb_operations import ADBDevice
import math
import subprocess
import re
from paddleocr import PaddleOCR
import numpy as np
import logging
"""
更新日志
V1.0
基础功能实现

V1.1~1.5
跟着游戏内容更新，适配界面更新

V1.6
1.兼容PVP第一次获胜的占卜弹窗
2.支持模拟器挂机，例如mumu：MuMuManager adb -v 0 connect通过cmd命令连接mumu模拟器

V2.0
1.引入百度PaddleOCR图像识别库，替换掉pytesseract，大幅提升文字识别准确度
2.pvp增加快速刷胜场模式，只跟人机对手进行对战

V2.1
1.修复战斗结束，竞技等级变化确认后，又弹出来玩偶宝箱的判定
2.调整第一次获胜后占卜界面的判定

V2.2
1.优化自动点个体值功能，能做到把一个60级以上精灵所有个体值都点满

V2.3
1.优化自动点个体值逻辑，当个体值点到50，会用个体值糖豆加

V2.4
1.增加PVP时自动使用技能的判定

V3.0
1.优化代码逻辑

V3.1
1.兼容最新版本更新后个体值按钮颜色变化
2.支持动态设置个体值点到多少后，再使用个体糖豆

V3.2
1.兼容6/17号最新版本更新后个体值按钮位置变化

V3.3
1.增加掉线保护，重新登录
2.增加顶号保护，重新登录
3.增加长久在线模式，支持自动好友电话pve

V3.4
1.优化精灵等级不足60级时，加个体值的兼容
2.增加不用道具的点个体值模式：个体值点到目标等级或精灵等级上限后自动切换下一行，最大个体值只需记录一次（每行上限相同）
"""

class fuke(ADBDevice):
    """电脑模拟器挂机，设置手机分辨率为1080*2400"""
    def __init__(self, device):
        ADBDevice.__init__(self, device)
        self.device_id = device
        self.bili = 1
        self.extra_distance = 0
        self.zhanli_repeat = 0
        self.ocr = PaddleOCR()
        logging.disable(logging.DEBUG)
        logging.disable(logging.WARNING)

    def analyse_pic_word(self, picname='', change_color=0):
        """识别图像中的文字, change_color=1或2为不同的二值化模式，其他不做处理"""
        try:
            path = os.path.dirname(__file__) + '/pic'
            if picname == '':
                pic = path + '/cut.png'
            else:
                pic = path + '/' + picname + '.png'
            img = Image.open(pic)
            img = img.convert('L')  # 转换为灰度图
            if change_color == 1:
                img = img.point(lambda x: 0 if x < 128 else 255)  # 二值化
            elif change_color == 2:
                img = img.point(lambda x: 0 if x < 251 else 255)  # 二值化
            # img.save(pic)
            img_np = np.array(img)  # 将 Image 对象转换为 numpy 数组
            result = self.ocr.ocr(img_np)
            if result == [None] or result is None:
                return ''
            return self.extract_ocr_content(result)
        except Exception as e:
            print(f"OCR识别异常: {e}")
            return ''

    def extract_ocr_content(self, content=[]):
        """对OCR识别到的内容进行取值和拼接，变成完整的一段内容"""
        ocr_result = content
        extracted_content = []
        for item in ocr_result[0]:  # item 的结构为 [位置信息, (识别内容, 置信度)]
            extracted_content.append(item[1][0])
        contains = ''.join(context for context in extracted_content if context)
        # print(contain)
        return contains

    def read_word(self, weizhi='up'):
        path = os.path.dirname(__file__) + '/pic'
        pic1_path = path + '/screenshot.png'
        pic = Image.open(pic1_path)
        cut_pic_path = path + '/cut.png'
        if weizhi == 'up':
            self.cut_pic((1068, 437), (1370, 510), '', 'pipeizhong')
            result = self.analyse_pic_word('pipeizhong', 0)
            if "匹配" in result:
                return 'battle'
            return ''
        elif weizhi == "competitor_name":  #对手的名字
            self.cut_pic((1266, 815), (1590, 875), '', 'competitor_name')
            result = self.analyse_pic_word('competitor_name')
            if result:
                print("对手：{}".format(result))
                return result
            print("未识别到对手信息")
            return ''
        elif weizhi == 'down':
            self.cut_pic((1090, 870), (1320, 970), '', 'zaixianpipei')
            result = self.analyse_pic_word('zaixianpipei', 0)
            if "线匹" in result:
                return 'battle'
            pic = Image.open(pic1_path)
            pic_new = pic.convert('RGBA')
            pix = pic_new.load()
            for y in range(910, 920):
                if 230 <= pix[1150, y][0] <= 250 and 170 <= pix[1150, y][1] <= 180 and 60 <= pix[1150, y][2] <= 84:
                    print('存在奖励确认窗口')
                    return 'reward'
            for y in range(885, 910):
                if 40 <= pix[1150, y][0] <= 60 and 170 <= pix[1150, y][1] <= 190 and 220 <= pix[1150, y][2] <= 240:
                    print('存在缎带确认窗口')
                    return 'duandai'  #精灵获得缎带的确认页面
            for y in range(950, 965):
                if 30 <= pix[1150, y][0] <= 90 and 160 <= pix[1150, y][1] <= 180 and 215 <= pix[1150, y][2] <= 240:
                    print('存在竞技等级确认窗口')
                    return 'level'  #竞技等级升级确认页面
            # pic.crop((int(1065 * self.bili + self.extra_distance), 872, int(1336 * self.bili + self.extra_distance),
            #           948)).save(cut_pic_path)  # 适用于找到 在线匹配 4个字框的下面的左半边部分
            # pic_new = Image.open(cut_pic_path)
            # pic_new = pic_new.convert('RGBA')
            # pix = pic_new.load()
            # # pic_new=pic_new.convert('1')  #convert方法可以将图片转成黑白
            # for y in range(pic_new.size[1]):  # 二值化处理，这个阈值为R=95，G=95，B=95
            #     for x in range(pic_new.size[0]):  # size[0]即图片长度，size[1]即图片高度
            #         # if 250 <= pix[x, y][0] <= 255 and 195 <= pix[x, y][1] <= 202 and pix[x, y][2] <= 18:  # 接近纯土黄色
            #         # if 235 <= pix[x, y][0] <= 255 and 95 <= pix[x, y][1] <= 115 and pix[x, y][2] <= 20:  # 接近纯土黄色
            #         #     return 'battle'
            #         if 22 <= pix[x, y][0] <= 30 and 16 <= pix[x, y][1] <= 24 and pix[x, y][2] <= 5:  # 有宝箱界面遮挡
            #             return 'valuebox'
            return ''
        elif weizhi == 'valuebox':  # 玩偶宝箱
            self.cut_pic((920, 250), (1500, 340), '', 'valuebox')
            result = self.analyse_pic_word('valuebox')
            if "获得一个" in result:
                return True
            return False
        # elif weizhi == 'level':
        #     pic.crop((int(890 * self.bili + self.extra_distance), 905, int(1020 * self.bili + self.extra_distance),
        #               980)).save(cut_pic_path)  # 适用于找到 确定 2个字
        #     pic_new = Image.open(cut_pic_path)
        #     pic_new = pic_new.convert('RGBA')
        #     pix = pic_new.load()
        #     for y in range(pic_new.size[1]):  # 二值化处理，这个阈值为R=95，G=95，B=95
        #         for x in range(pic_new.size[0]):  # size[0]即图片长度，size[1]即图片高度
        #             if 14 <= pix[x, y][0] <= 56 and 160 <= pix[x, y][1] <= 174 and 238 <= pix[x, y][2] <= 248:
        #                 return 'OK'
        #     return ''
        elif weizhi == 'taopao':  # 对方已经退出!
            self.cut_pic((1025, 430), (1350, 500), '', 'yitaopao')
            result = self.analyse_pic_word('yitaopao')
            if "已经退出" in result:
                return True
            elif "逃跑" in result:
                return True
            return False
        elif weizhi == 'diaoxian':  # 已经掉线!
            self.cut_pic((1025, 430), (1350, 500), '', 'yidiaoxian')
            result = self.analyse_pic_word('yidiaoxian')
            if "掉线" in result:
                return True
            if "已断开" in result:
                return True
            return False
        elif weizhi == 'caozuopinfan':  # 操作频繁的提醒!
            self.cut_pic((808, 410), (1600, 530), '', 'caozuopinfan')
            result = self.analyse_pic_word('caozuopinfan')
            if "慢点" in result:
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
            self.cut_pic((1467, 777), (1670, 846), '', 'zhanbu')
            result = self.analyse_pic_word('zhanbu')
            if "占卜" in result:
                return True
            return False
        elif weizhi == 'geti_confirm':
            self.cut_pic((1150, 750), (1250, 805), '', 'geti_confirm')
            result = self.analyse_pic_word('geti_confirm')
            if "确定" in result:
                return True
            return False
        elif weizhi == 'use_geti_item':
            self.cut_pic((1100, 660), (1290, 720), '', 'use_geti_item')
            result = self.analyse_pic_word('use_geti_item')
            if "道具" in result:
                return True
            return False

    def check_and_click_skill(self):
        """检测并自动点击技能位置"""
        path = os.path.dirname(__file__) + '/pic'
        pic_path = path + '/screenshot.png'
        img = Image.open(pic_path)
        img_rgba = img.convert('RGBA')
        pix = img_rgba.load()
        
        # 技能位置配置：4个位置，X间隔303，从左到右
        skill_positions = [(373, 1000), (676, 1000), (979, 1000), (1282, 1000)]
        target_color = (99, 214, 58)
        color_tolerance = 10  # 颜色容差
        
        for x, y in skill_positions:
            r, g, b = pix[x, y][0], pix[x, y][1], pix[x, y][2]
            if (abs(r - target_color[0]) <= color_tolerance and
                abs(g - target_color[1]) <= color_tolerance and
                abs(b - target_color[2]) <= color_tolerance):
                self.click(x, y)
                print(f"检测到技能克制，位置({x},{y})，点击成功")
                return True
        return False

    def _handle_reward_dialog(self, x):
        """处理奖励确认弹窗"""
        self.click(x, 906)
        print('点击确认奖励')
        time.sleep(1)
        return True

    def _handle_duandai_dialog(self, x):
        """处理缎带奖励弹窗"""
        self.click(x, 880)
        print('点击确认缎带奖励')
        time.sleep(1)
        return True

    def _handle_level_dialog(self, x):
        """处理竞技等级升降弹窗"""
        self.click(x, 950)
        print('点击确认等级升降')
        time.sleep(2)
        self.get_screenshot('pic')
        if self.read_word('valuebox'):
            self.click(x, 572)  # 宝箱位置
            print('点击打开玩偶宝箱')
            time.sleep(3)
            self.get_pic()
            print('保存玩偶宝箱获取的截图.')
            self.click(x, 900)  # 确定
            print('点击确认')
            time.sleep(1)
        return True

    def _handle_hailuo_dialog(self, x):
        """处理海螺结算弹窗"""
        self.click(x, 762)  # 点击海螺确定界面
        print("Click close hailuo screen.")
        time.sleep(1)
        self.get_screenshot('pic')
        if self.read_word('down') == 'battle':
            print('Battle end')
            return 'battle_end'
        elif self.read_word('valuebox'):
            self.click(x, 572)  # 宝箱位置
            print('点击打开玩偶宝箱')
            time.sleep(3)
            self.get_pic()
            print('保存玩偶宝箱获取的截图.')
            self.click(x, 900)  # 确定
            print('Click confirm button')
            time.sleep(1)
            return 'reward_handled'
        return None

    def _handle_valuebox_dialog(self, x):
        """处理玩偶宝箱弹窗"""
        self.click(x, 572)  # 宝箱位置
        print('点击打开玩偶宝箱')
        time.sleep(3)
        self.get_pic()
        print('保存玩偶宝箱获取的截图.')
        self.click(x, 900)  # 确定
        print('Click confirm button')
        time.sleep(1)
        return True

    def _handle_zhanbu_dialog(self, x):
        """处理占卜弹窗"""
        self.click(1570, 815)  # 占卜位置
        print('点击确认占卜')
        time.sleep(3)
        self.click(x, 900)  # 确定
        print('点击确认')
        time.sleep(1)
        self.click(1910, 110)  # 关闭占卜
        print('点击关闭占卜弹窗')
        time.sleep(2)
        return True

    def _handle_battle_end_check(self, x, str1):
        """检查并处理战斗结束的各种弹窗，返回是否结束战斗"""
        down_result = self.read_word('down')
        if down_result == 'battle':
            print('Battle end')
            return 'battle_end'
        elif down_result == 'reward':
            self._handle_reward_dialog(x)
            return 'battle_end'
        elif down_result == 'duandai':
            self._handle_duandai_dialog(x)
            return 'battle_end'
        elif down_result == 'level':
            self._handle_level_dialog(x)
            return 'battle_end'

        if self.read_word('hailuo'):
            result = self._handle_hailuo_dialog(x)
            if result in ('battle_end', 'reward_handled'):
                return result

        if self.read_word('valuebox'):
            self._handle_valuebox_dialog(x)
            return 'battle_end'

        if self.read_word('zhanbu'):
            self._handle_zhanbu_dialog(x)
            return 'continue'

        return 'continue'

    def duizhan_battle(self, id='1163746998', only_robot=False, quick_battle=False):
        """only_robot参数为Ture会只与人机对战，quick_battle参数为Ture会主动释放技能"""
        for i in range(200):
            x = int(1200 * self.bili + self.extra_distance)
            self.click(x, 900)  # 点在线匹配
            print("点击 %s 917 开始匹配." % x)
            time.sleep(5)  # 刚开始匹配多等一会
            self.get_screenshot('pic')
            count = 0
            while 'battle' in self.read_word('up') and count < 28:
                time.sleep(3)  # 每3秒截屏
                self.get_screenshot('pic')
                count += 1
            if count == 40:
                self.click(x, 568)  # 点击取消
                print('长时间匹配不到对手，点击取消匹配')
                time.sleep(1)
                continue

            competitor = self.read_word('competitor_name')
            if only_robot:
                if "大世界" in competitor:
                    # 包含大世界，非人机，跳过
                    print('非人机对手，直接不点击开始，跳过战斗')
                    time.sleep(20)
                elif "的" in competitor:
                    # 包含的，人机，开始战斗
                    self.click(x, 532)
                    print('匹配到对手，开始决斗!')
                else:
                    # 其他情况，非人机，跳过
                    print('非人机对手，直接不点击开始，跳过战斗')
                    time.sleep(20)
            else:
                self.click(x, 532)  # 点击开始
                print('匹配到对手，开始决斗!')

            for i in range(80):
                time.sleep(5)  # 2分钟对战
                self.get_screenshot('pic')
                if quick_battle:
                    self.check_and_click_skill()  # 检测并点击技能

                # 处理逃跑和掉线
                if self.read_word('taopao'):
                    self.click(x, 615)
                    print("对方已逃跑!")
                    self.delay(2)
                    self.get_screenshot('pic')
                elif self.read_word('diaoxian'):
                    self.click(x, 615)
                    print("确认已掉线!")
                    self.delay(2)
                    self.get_screenshot('pic')

                if self.read_word('caozuopinfan'):
                    self.click(x, 640)
                    print("确认操作频繁!")
                    self.delay(2)
                    self.get_screenshot('pic')

                # 处理战斗结束弹窗
                result = self._handle_battle_end_check(x, 'battle')
                if result == 'battle_end':
                    break

    def swipe(self, device_id, left_up_x=0, left_up_y=0, right_down_x=1080, right_down_y=1500, steps=200):
        """划动屏幕"""
        os.system("adb -s {} shell input swipe {} {} {} {} {}".format(device_id, left_up_x, left_up_y, right_down_x, right_down_y, steps))

    def add_geti(self, target_level=50, use_item=True):
        """自动点击精灵个体值
        use_item=True: 个体值到达目标等级后使用个体值糖豆继续加点
        use_item=False: 不用道具模式，个体值到达目标等级或精灵等级上限后切换下一行
        （精灵等级不足60时，个体值上限为精灵等级，而非60）
        """
        swipe_times = 0
        max_geti_value = None  # 不用道具模式：个体值可到达的最大值（每行都相同，只需记录一次）
        for i in range(360):
            self.get_screenshot('pic')
            path = os.path.dirname(__file__) + '/pic'
            pic_path = path + '/screenshot.png'
            img = Image.open(pic_path)
            img_rgba = img.convert('RGBA')
            pix = img_rgba.load()
            # 扫描所有个体值按钮的行坐标（相邻匹配像素合并为同一行）
            row_ys = []
            last_y = -100
            for y in range(330, 870):
                if 60 < pix[2022, y][0] <= 100 and 180 <= pix[2022, y][1] <= 205 and 210 <= pix[2022, y][2] <= 220:
                    if y - last_y > 10:
                        row_ys.append(y)
                    last_y = y
            can_find_geti = False
            for y in row_ys:
                if not use_item:
                    # 不用道具模式：已记录最大值后，该行个体值达到最大值直接切换下一行
                    if max_geti_value is not None:
                        current_value = self.read_geti_value(y)
                        # 读取出错时视为已到上限，避免重复点击无反应的行
                        if current_value is None or current_value >= max_geti_value:
                            print(f"y={y}行个体值已到达最大值{max_geti_value}，直接切换下一行")
                            continue
                    # 不用道具模式：到达目标等级后不使用道具，切换下一行
                    if self.check_level_reached(y, target_level):
                        print(f"该行个体值已到达目标等级{target_level}，切换下一行")
                        if max_geti_value is None:
                            max_geti_value = target_level
                            print(f"记录个体值最大值为{max_geti_value}")
                        continue
                    can_find_geti = True
                    print(f"找到y对应坐标{y}")
                    current_value = self.read_geti_value(y)
                    self.click(2022, y)
                    print("点击增加个体值")
                    self.delay(1)
                    self.get_screenshot('pic')
                    if self.read_word("geti_confirm"):
                        self.click(1200, 775)
                        print("点击确定加1点个体值")
                        self.delay(1)
                        self.click(1020, 640)
                        print("点击二次确定加个体值")
                        print("等待5分钟个体值恢复")
                        self.delay(300)
                    elif self.read_word("use_geti_item"):
                        # 弹出使用道具提示，说明免费加点已到上限，取消并切换下一行
                        self.click(1466, 694)
                        print("点击取消使用个体值道具")
                        self.delay(10)
                        if max_geti_value is None:
                            max_geti_value = current_value if current_value is not None else self.read_geti_value(y)
                            print(f"记录个体值最大值为{max_geti_value}")
                        print("该行个体值已到上限，切换下一行")
                        continue
                    else:
                        # 点击后没有弹出geti_confirm，说明个体值已到精灵等级上限（如等级50，个体值50）
                        if max_geti_value is None:
                            max_geti_value = current_value if current_value is not None else self.read_geti_value(y)
                            print(f"记录个体值最大值为{max_geti_value}")
                        print(f"点击未弹出确认框，该行个体值已到精灵等级上限{max_geti_value}，切换下一行")
                        continue
                    break
                # 使用道具模式
                can_find_geti = True
                print(f"找到y对应坐标{y}")

                # 检查是否到达目标等级（个体值已满）
                is_target_reached = self.check_level_reached(y, target_level)

                # 如果已达到目标等级，直接点击后使用道具，跳过加1点流程
                if is_target_reached:
                    print(f"该个体值到达目标等级{target_level}，直接使用道具")
                    self.click(2022, y)
                    print("点击增加个体值")
                    self.delay(1)
                    self.use_geti_item()
                else:
                    # 未达到目标等级，走正常加1点流程
                    self.click(2022, y)
                    print("点击增加个体值")
                    self.delay(1)
                    self.get_screenshot('pic')
                    if self.read_word("geti_confirm"):
                        self.click(1200, 775)
                        print("点击确定加1点个体值")
                        self.delay(1)
                        self.click(1020, 640)
                        print("点击二次确定加个体值")
                        print("等待5分钟个体值恢复")
                        self.delay(300)
                    elif self.read_word("use_geti_item"):
                        self.click(1466,694)
                        print("点击取消使用个体值道具")
                        self.delay(10)
                    else:
                        self.delay(5)
                        self.click(2022, y)
                        print("点击增加个体值")
                        self.delay(2)
                        self.get_screenshot('pic')
                        if self.read_word("geti_confirm"):
                            self.click(1200, 745)
                            print("点击确定加1点个体值")
                            self.delay(1)
                            self.click(1020, 640)
                            print("点击二次确定加个体值")
                            print("等待5分钟个体值恢复")
                            self.delay(300)
                break
            if not can_find_geti and swipe_times<=2:
                self.swipe(self.device_id, 2022, 750, 2022, 350)
                print("上划个体值条")
                swipe_times +=1
                self.delay(2)
            elif not can_find_geti and not use_item:
                print("所有个体值均已到达目标等级或精灵等级上限，结束")
                break

    def read_geti_value(self, y):
        """读取该行当前个体值数值，读取失败返回None"""
        self.cut_pic((1830, y - 15), (1960, y + 25), '', 'geti_value_check')
        result = self.analyse_pic_word('geti_value_check', 0)
        print(f"检测到个体值文字: {result}")
        nums = re.findall(r'\d+', result)
        if nums:
            return int(nums[0])
        return None

    def check_level_reached(self, y, target_level=50):
        """检查指定y坐标位置是否显示目标等级"""
        self.cut_pic((1830, y-15), (1960, y+25), '', 'level_target_check')
        result = self.analyse_pic_word('level_target_check', 0)
        print(f"检测到等级文字: {result}")
        target_str = str(target_level)
        if target_str in result or f"等级{target_str}" in result:
            print(f"确认该行个体值已到目标等级{target_level}")
            return True
        return False

    def use_geti_item(self):
        """使用个体值道具（个体值糖豆）"""
        # 点击使用道具按钮
        self.click(901, 745)
        print("点击使用道具按钮")
        self.delay(2)
        self.get_screenshot('pic')
        # 寻找个体值糖豆位置（3个位置依次检测）
        y_positions = [275, 485, 695]  # 三个检测位置的y起始坐标
        target_y = None
        
        for y_start in y_positions:
            self.cut_pic((690, y_start), (900, y_start + 70), '', 'geti_item_text')
            result = self.analyse_pic_word('geti_item_text', 0)
            print(f"检测道具位置 y={y_start}-{y_start+70}: {result}")
            if "个体值糖豆" in result or "糖豆" in result:
                target_y = y_start + 35  # 取y范围的中间值
                print(f"找到个体值糖豆，y中心坐标: {target_y}")
                break
        
        if target_y is None:
            print("未找到个体值糖豆，取消操作")
            # 点击取消/关闭按钮返回
            self.click(1880, 157)
            self.delay(1)
            return
        
        # 点击对应位置的"使用道具"按钮
        use_btn_y = target_y + 20
        self.click(1805, use_btn_y)
        print(f"点击y={use_btn_y}位置的使用道具按钮")
        self.delay(1)
        
        # 确认使用
        self.click(1200, 840)
        print("确认使用个体值糖豆")
        self.delay(1)
        self.click(1035, 640)
        print("二次确认使用个体值糖豆")
        self.delay(1)
        self.click(1035, 640)
        print("随便点一下关闭消息")
        self.delay(1)
        print("关闭使用道具的界面")
        self.click(1880, 157)
        self.delay(2)

    def kill_game(self):
        """强制停止游戏应用"""
        package = 'com.pock.maichi'
        os.system(self._adb("shell am force-stop %s" % package))
        print("已强制停止游戏进程: %s" % package)
        self.delay(3)

    def restart_game(self):
        """重启游戏：先kill掉应用，再重新启动"""
        print("正在重启游戏...")
        self.kill_game()
        print("游戏已关闭，等待5秒后重新启动...")
        self.delay(5)
        self.start_game()
        print("游戏重启完成")

    def start_game(self):
        """启动游戏应用"""
        os.system(self._adb("shell am start com.pock.maichi/com.entry.MainActivity"))
        self.delay(10)
        for i in range(30):
            self.get_screenshot('pic')
            self.cut_pic((1293, 916), (1431, 973), '', 'start_queding')
            result = self.analyse_pic_word('start_queding', 0)
            if "确定" in result:
                self.click(1367, 947)
                print("识别到确定，点击确定")
                # 登录流程
                self.delay(6)
                self.get_screenshot()
                self.cut_pic((1331, 241), (1627, 315), '', 'login_phone')
                result2 = self.analyse_pic_word('login_phone', 0)
                if "手机登录" in result2:
                    print("识别到手机登录，点账号登录")
                    self.click(923, 281)
                    self.delay(1)
                    self.click(1631, 420)
                    self.delay(2)
                    self.get_screenshot()
                    self.cut_pic((787, 507), (1057, 573), '', 'login_account')
                    result3 = self.analyse_pic_word('login_account', 0)
                    if "189" in result3:
                        print("识别到189账号，选择该账号")
                        self.click(866, 540)
                    else:
                        print("未识别到189账号，选择其他账号")
                        self.click(866, 640)
                    self.delay(3)
                    self.click(897, 484)
                self.delay(5)
                self.click(1210, 955)
                print("点击进入游戏")
                break
            self.delay(10)
        self.delay(10)

    def get_current_time(self):
        now = datetime.now().strftime("%H")
        print(now)

    def select_device(self):
        """选择设备"""
        string = subprocess.Popen('adb devices', shell=True, stdout=subprocess.PIPE)
        totalstring = string.stdout.read()
        totalstring = totalstring.decode('utf-8')
        # print(totalstring)
        # devicelist = re.compile(r'(\w*)\s*device\b').findall(totalstring)
        pattern = r'(\b(?:[0-9]{1,3}(?:\.[0-9]{1,3}){3}(?::[0-9]+)?|[A-Za-z0-9]{8,})\b)\s*device\b'
        devicelist = re.findall(pattern, totalstring)
        devicenum = len(devicelist)
        if devicenum == 0:
            print("当前没有设备连接!")
            return False
        elif devicenum == 1:
            print("当前只有一台设备:%s." % devicelist[0])
            return devicelist[0]
        else:
            print("当前存在多台设备，请选择设备:")
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
                print('请输入正确的数字!')
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
        print("Input the num to select function! \n" \
              "1 自动 PVP\n" \
              "2 自动 点个体值\n"
              "3 自动 PVP(只打人机)\n"
              "4 自动在线(每天23:00和5:00重启游戏)\n"
              "5 自动 点个体值(不用道具)\n")
        num = input()
        if num == '1':
            self.duizhan_battle(self.device_id, False, True)
        elif num == '2':
            self.add_geti(55)
        elif num == '3':
            self.duizhan_battle(self.device_id, True, True)
        elif num == '4':
            self.auto_online()
        elif num == '5':
            self.add_geti(55, use_item=False)

    def auto_online(self):
        """自动在线：每天23:00和4:00重启游戏，同时每10分钟监测好友PVE来电"""
        from datetime import datetime
        print("自动在线模式已启动，将在每天23:00和4:00重启游戏...")
        last_pve_check = 0  # 上次PVE检测时间戳
        while True:
            now = datetime.now()
            current_hour = now.hour
            current_minute = now.minute
            # 到达23:00或4:00时执行重启
            if (current_hour == 23 or current_hour == 4) and current_minute == 0:
                print("当前时间 %s，开始重启游戏..." % now.strftime('%H:%M:%S'))
                self.restart_game()
                # 4点重启后检查签到奖励
                if current_hour == 4:
                    self.delay(10)
                    self.check_sign_reward()
                print("重启完成，等待下一轮...")
                self.delay(120)  # 重启后等待2分钟避免重复触发
            # 每10分钟检测好友PVE来电
            import time
            current_ts = time.time()
            if current_ts - last_pve_check >= 600:
                last_pve_check = current_ts
                self.check_friend_pve()
            self.delay(30)  # 每30秒检查一次时间

    def check_sign_reward(self):
        """检查并关闭签到奖励弹窗"""
        print("检查签到奖励...")
        self.get_screenshot()
        self.cut_pic((972, 150), (1337, 252), '', 'sign_reward')
        result = self.analyse_pic_word('sign_reward', 0)
        if "签到奖励" in result:
            print("识别到签到奖励，关闭弹窗")
            self.click(2070, 50)
        else:
            print("无签到奖励弹窗")

    def check_friend_pve(self):
        """监测好友PVE来电提醒"""
        print("检测好友PVE来电...")
        self.get_screenshot()
        self.cut_pic((580, 420), (760, 470), '', 'pve_laidian')
        result = self.analyse_pic_word('pve_laidian', 0)
        if "来电提醒" in result:
            print("识别到来电提醒，点击接听")
            self.click(667, 445)
            self.delay(4)
            self.get_screenshot()
            self.click(800, 1010)
            self.delay(2)
            self.get_screenshot()
            self.cut_pic((650, 370), (810, 420), '', 'pve_tiaozhan')
            result2 = self.analyse_pic_word('pve_tiaozhan', 0)
            if "发起挑战" in result2:
                print("识别到发起挑战，点击挑战")
                self.click(734, 397)
                self.delay(10)
                self.get_screenshot()
                self.cut_pic((1950, 110), (2080, 160), '', 'pve_auto')
                result3 = self.analyse_pic_word('pve_auto', 0)
                if "自动" in result3:
                    print("未开启自动，点击自动")
                    self.click(2012, 98)
                else:
                    print("已开启自动")
                self.delay(20)
                self.click(2097, 523)
                print("PVE战斗结束，退出")
            else:
                print("未识别到发起挑战，跳过")
        else:
            print("无来电提醒")

if __name__ == '__main__':
    test = fuke('')
    test.start_play()
