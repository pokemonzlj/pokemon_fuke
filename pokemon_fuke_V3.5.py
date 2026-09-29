# -*-coding:utf-8-*-
import os
import sys
from PIL import Image
import time
import threading
import _thread
from datetime import datetime
from PIL import ImageGrab, Image, ImageOps
from adb_operations import ADBDevice
import math
import subprocess
import re
import random
import cv2
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
3.PVP中可使用极巨化时，先极巨化再重新判断技能克制关系

V3.5
1.进一步优化技能使用，选择最合适的技能释放
2.当存在极巨化、极晶化，会使用
3.优化早上登录，自动签到、自动转盘抽奖
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

    def _recognize_transformation_button(self, img):
        """用OCR识别变身按钮，返回dynamax/terastallize/None。"""
        # 极巨化、极晶化和展开后的“取消”会共用近似区域。
        # 颜色和特效会互相污染，因此只以按钮文字作为变身依据。
        button_region = img.convert('RGB').crop((1000, 690, 1420, 850))
        button_region = button_region.resize(
            (button_region.width * 2, button_region.height * 2),
            Image.Resampling.LANCZOS
        )
        variants = [
            button_region,
            ImageOps.autocontrast(button_region.convert('L')),
        ]

        recognized_parts = []
        for variant in variants:
            try:
                result = self.ocr.ocr(np.array(variant))
                if result and result != [None]:
                    text = self.extract_ocr_content(result)
                    if text:
                        recognized_parts.append(text)
            except Exception as e:
                print(f"变身按钮OCR识别异常: {e}")
                return None

        button_text = re.sub(r'\s+', '', ''.join(recognized_parts))
        if "取消" in button_text:
            print("变身按钮OCR识别: 取消，不执行变身")
            return None

        has_dynamax = "极巨化" in button_text
        has_terastallize = "极晶化" in button_text
        if has_dynamax and has_terastallize:
            print(f"变身按钮OCR结果冲突，不执行变身: {button_text}")
            return None
        if has_dynamax:
            print(f"变身按钮OCR识别: {button_text}")
            return 'dynamax'
        if has_terastallize:
            print(f"变身按钮OCR识别: {button_text}")
            return 'terastallize'
        return None

    def _ocr_region(self, img, box):
        """识别截图指定区域内的文字。"""
        region = img.convert('RGB').crop(box)
        region = region.resize(
            (region.width * 2, region.height * 2),
            Image.Resampling.LANCZOS
        )
        try:
            result = self.ocr.ocr(np.array(region))
            if result and result != [None]:
                return self.extract_ocr_content(result)
        except Exception as e:
            print(f"精灵选择页OCR识别异常: {e}")
        return ''

    def _find_ocr_text_centers(self, img, box, keyword):
        """返回指定区域内包含关键词的OCR文字中心坐标。"""
        region = img.convert('RGB').crop(box)
        try:
            result = self.ocr.ocr(np.array(region))
        except Exception as e:
            print(f"OCR按钮定位异常: {e}")
            return []

        centers = []
        if not result or result == [None] or not result[0]:
            return centers

        for points, (text, confidence) in result[0]:
            normalized_text = re.sub(r'\s+', '', text)
            if keyword not in normalized_text:
                continue
            center_x = int(sum(point[0] for point in points) / len(points) + box[0])
            center_y = int(sum(point[1] for point in points) / len(points) + box[1])
            centers.append((center_x, center_y))
        return centers

    def _find_advantaged_pokemon(self, img):
        """在精灵选择页中返回第一个带绿色上箭头的精灵卡片坐标。"""
        img_rgb = img.convert('RGB')
        pokemon_cards = [
            ((850, 370), (620, 350)),
            ((1420, 370), (1200, 350)),
            ((1990, 370), (1780, 350)),
            ((850, 720), (620, 700)),
            ((1420, 720), (1200, 700)),
            ((1990, 720), (1780, 700)),
        ]

        for (arrow_x, arrow_y), card_position in pokemon_cards:
            region = img_rgb.crop((arrow_x - 50, arrow_y - 70, arrow_x + 50, arrow_y + 70))
            green_pixels = sum(
                1 for r, g, b in region.getdata()
                if r <= 130 and g >= 140 and b >= 100 and g >= r * 1.25
            )
            if green_pixels >= 100:
                return card_position
        return None

    def _is_pokemon_confirmation(self, img):
        """通过左侧“确定”按钮文字识别精灵切换确认弹窗。"""
        confirm_button_text = self._ocr_region(img, (850, 520, 1150, 700))
        return "确定" in confirm_button_text

    def _handle_pokemon_selection(self, img):
        """处理PVP中主动或阵亡后出现的精灵选择页。"""
        title = self._ocr_region(img, (300, 100, 850, 240))
        if "选择精灵" not in title:
            return False

        if self._is_pokemon_confirmation(img):
            self.click(1030, 615)
            print("识别到精灵出战确认弹窗，已点击确定")
            return True

        pokemon_position = self._find_advantaged_pokemon(img)
        if not pokemon_position:
            print("已进入精灵选择页，未发现克制精灵，等待系统自动选择")
            return True

        self.click(*pokemon_position)
        print(f"检测到克制精灵，已点击精灵卡片{pokemon_position}")
        time.sleep(0.5)
        self.get_screenshot('pic')
        path = os.path.dirname(__file__) + '/pic/screenshot.png'
        confirm_img = Image.open(path)
        if self._is_pokemon_confirmation(confirm_img):
            self.click(1030, 615)
            print("已点击确定，完成精灵切换")
        else:
            print("已选择克制精灵，暂未识别到确认弹窗")
        return True

    def _open_pokemon_selection(self):
        """点击技能栏右侧的精灵按钮并尝试处理选择页。"""
        self.click(1650, 950)
        print("可用技能均为抵抗或无效，已点击精灵按钮")
        time.sleep(0.5)
        self.get_screenshot('pic')
        path = os.path.dirname(__file__) + '/pic/screenshot.png'
        self._handle_pokemon_selection(Image.open(path))
        return True

    def _classify_skills(self, img):
        """识别四个技能的状态：advantaged/neutral/resisted/invalid。"""
        skill_positions = [(373, 1000), (676, 1000), (979, 1000), (1282, 1000)]
        advantaged_color = (99, 214, 58)   # 绿色上箭头
        resisted_color = (216, 76, 59)     # 红色下箭头
        color_tolerance = 12
        img_rgb = img.convert('RGB')
        skills = []

        # 箭头会因动画和抗锯齿有少量偏移，扫描按钮上半部而不只取一个像素。
        for x, y in skill_positions:
            invalid_region = img_rgb.crop((x - 135, y - 100, x + 135, y + 40))
            invalid_pixels = sum(
                1 for r, g, b in invalid_region.getdata()
                if 180 <= r <= 245 and g <= 35 and b <= 50
            )

            left = max(0, x - 60)
            top = max(0, y - 80)
            right = min(img_rgb.width, x + 60)
            bottom = min(img_rgb.height, y + 30)
            region = img_rgb.crop((left, top, right, bottom))
            advantaged_pixels = sum(
                1 for r, g, b in region.getdata()
                if (abs(r - advantaged_color[0]) <= color_tolerance and
                    abs(g - advantaged_color[1]) <= color_tolerance and
                    abs(b - advantaged_color[2]) <= color_tolerance)
            )
            resisted_pixels = sum(
                1 for r, g, b in region.getdata()
                if (abs(r - resisted_color[0]) <= color_tolerance and
                    abs(g - resisted_color[1]) <= color_tolerance and
                    abs(b - resisted_color[2]) <= color_tolerance)
            )

            # “无效”斜章的深红色与抵抗箭头不同，且覆盖面积更大。
            # 无效状态的优先级最高，避免斜章中其他颜色导致误判为箭头。
            if invalid_pixels >= 100:
                effectiveness = 'invalid'
            elif advantaged_pixels >= 50:
                effectiveness = 'advantaged'
            elif resisted_pixels >= 50:
                effectiveness = 'resisted'
            else:
                effectiveness = 'neutral'
            skills.append((effectiveness, (x, y)))

        return skills

    def _find_skill(self, skills, effectiveness):
        """按从左到右的顺序返回指定克制关系的第一个技能。"""
        for current_effectiveness, position in skills:
            if current_effectiveness == effectiveness:
                return position
        return None

    def _choose_skill(self, skills):
        """排除无效技能，按“克制 > 随机普通 > 抵抗”选择技能。"""
        skill_position = self._find_skill(skills, 'advantaged')
        if skill_position:
            return 'advantaged', skill_position

        neutral_skills = [
            position for effectiveness, position in skills
            if effectiveness == 'neutral'
        ]
        if neutral_skills:
            return 'neutral', random.choice(neutral_skills)

        return 'switch', None

    def _is_skill_bar_visible(self, img):
        """检测当前是否已显示完整的四技能栏。"""
        img_rgb = img.convert('RGB')
        skill_x_positions = (373, 676, 979, 1282)
        visible_cards = 0

        # 四张技能卡的标题区域都有大面积亮色背景。先确认技能栏存在，
        # 避免在战斗动画或结算弹窗中把“没有箭头”误当成普通技能。
        for x in skill_x_positions:
            region = img_rgb.crop((x - 105, 860, x + 105, 930))
            bright_pixels = sum(
                1 for r, g, b in region.getdata()
                if r >= 225 and g >= 225 and b >= 215
            )
            if bright_pixels >= 5000:
                visible_cards += 1

        return visible_cards >= 3

    def check_and_click_skill(self):
        """检测极巨化和技能克制关系，并按对战规则点击。"""
        path = os.path.dirname(__file__) + '/pic'
        pic_path = path + '/screenshot.png'
        img = Image.open(pic_path)

        # 精灵阵亡时会直接进入选择页，必须在技能和变身判定前优先处理。
        if self._handle_pokemon_selection(img):
            return True

        transformation = self._recognize_transformation_button(img)

        if transformation == 'dynamax':
            if not self._is_skill_bar_visible(img):
                return False

            # 极巨化后技能图标会改变，不再用新图标的颜色重新判定。
            # 先根据极巨化前的箭头选定技能，极巨化后直接点击同一槽位。
            skill_type, skill_position = self._choose_skill(self._classify_skills(img))
            if skill_type == 'switch':
                return self._open_pokemon_selection()
            self.click(1235, 775)
            print("检测到极巨化按钮，已点击极巨化")
            time.sleep(0.5)
            self.get_screenshot('pic')
            self.click(*skill_position)
            print(f"极巨化前已选定{skill_type}技能{skill_position}，极巨化后按原槽位使用")
            return True
        elif transformation == 'terastallize':
            self.click(1165, 775)
            print("检测到极晶化按钮，已点击极晶化")
            time.sleep(0.5)
            self.get_screenshot('pic')
            img = Image.open(pic_path)
            self.click(1335, 680)
            print("已选择极晶化属性列表最右侧的一般属性")

        if not self._is_skill_bar_visible(img):
            return False

        skills = self._classify_skills(img)
        skill_type, skill_position = self._choose_skill(skills)
        if skill_type == 'switch':
            return self._open_pokemon_selection()
        if skill_type == 'advantaged':
            self.click(*skill_position)
            print(f"检测到技能克制，位置{skill_position}，点击成功")
            return True
        elif skill_type == 'neutral':
            self.click(*skill_position)
            print(f"未检测到克制技能，随机使用普通技能{skill_position}")
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

    def _handle_insufficient_pokemon_dialog(self):
        """处理首次匹配时“出战精灵不足6只”的登录期提示弹窗。"""
        self.get_screenshot('pic')
        path = os.path.dirname(__file__) + '/pic/screenshot.png'
        img = Image.open(path)
        dialog_text = self._ocr_region(img, (700, 300, 1650, 520))
        if "不足6只" not in dialog_text and "继续匹配" not in dialog_text:
            return False

        confirm_buttons = self._find_ocr_text_centers(
            img, (850, 550, 1250, 750), "确定"
        )
        if not confirm_buttons:
            print("识别到出战精灵不足弹窗，但未识别到确定按钮")
            return False

        self.click(1029, 527)
        print("已勾选“本次登录不再提示”")
        self.delay(0.5)
        self.click(*confirm_buttons[0])
        print(f"已点击出战精灵不足弹窗的确定按钮{confirm_buttons[0]}")
        self.delay(1)
        return True

    def duizhan_battle(self, id='1163746998', only_robot=False, quick_battle=False,
                       scheduled_stop_hour=None):
        """执行PVP；scheduled_stop_hour仅供定时流程在指定小时停止使用。"""
        for i in range(200):
            if self._scheduled_pvp_stop_reached(scheduled_stop_hour):
                print(f"已到{scheduled_stop_hour}:00，停止定时自动PVP")
                return 'scheduled_stop'

            x = int(1200 * self.bili + self.extra_distance)
            self.click(x, 900)  # 点在线匹配
            print("点击 %s 917 开始匹配." % x)
            if i == 0:
                self.delay(1)
                self._handle_insufficient_pokemon_dialog()
                time.sleep(4)
            else:
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

            if self._scheduled_pvp_stop_reached(scheduled_stop_hour):
                print(f"已到{scheduled_stop_hour}:00，本次匹配不点击开始，等待匹配自动结束")
                self.delay(20)
                return 'scheduled_stop'

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

            # 16点到达时不在战斗中强行关闭页面；完成当前场后再退出。
            if self._scheduled_pvp_stop_reached(scheduled_stop_hour):
                print(f"当前场次已结束，停止{scheduled_stop_hour}:00后的定时自动PVP")
                return 'scheduled_stop'

    def _scheduled_pvp_stop_reached(self, stop_hour):
        """定时PVP是否已到停止时刻；普通PVP不传参数，不受该限制。"""
        return stop_hour is not None and datetime.now().hour >= stop_hour

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
              "4 自动在线(23:00和4:00重启，定时领体力，12:00-16:00纯人机PVP)\n"
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
        """自动在线：定时重启、领取体力、监测好友PVE并在中午后自动PVP。"""
        from datetime import datetime
        print("自动在线模式已启动：每天23:00和4:00重启，12:00-14:00和18:00-20:00领取体力，12:00-16:00自动PVP...")
        last_periodic_check = 0  # 上次十分钟巡检时间戳
        completed_stamina_slot = None
        completed_pvp_date = None
        while True:
            now = datetime.now()
            current_hour = now.hour
            current_minute = now.minute
            current_ts = time.time()
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

            # 所有追加的挂机任务统一每10分钟巡检一次。
            if current_ts - last_periodic_check >= 600:
                last_periodic_check = current_ts
                stamina_slot = self._get_stamina_claim_slot(now)
                if stamina_slot and stamina_slot != completed_stamina_slot:
                    if self.claim_scheduled_stamina(stamina_slot):
                        completed_stamina_slot = stamina_slot
                self.check_friend_pve()

                # 自动PVP必须在当天12点档体力领取流程完成后启动。
                current_date_key = now.strftime('%Y-%m-%d')
                stamina_completed_today = (
                    completed_stamina_slot is not None
                    and completed_stamina_slot.startswith(current_date_key + ':')
                )
                if (12 <= now.hour < 16 and stamina_completed_today
                        and completed_pvp_date != current_date_key):
                    if self.prepare_scheduled_pvp():
                        # 进入现有PVP循环前先记为完成，避免循环返回后当天重复初始化。
                        completed_pvp_date = current_date_key
                        print("阵容准备完成，启动纯人机自动PVP模式")
                        pvp_result = self.duizhan_battle(
                            self.device_id, True, True, scheduled_stop_hour=16
                        )
                        if pvp_result == 'scheduled_stop':
                            self.click(2070, 50)
                            print("已点击右上角X，退出PVP对战中心")
                            self.delay(1)
            self.delay(30)  # 每30秒检查一次时间

    def _get_stamina_claim_slot(self, now):
        """返回当前应执行的每日体力领取时段标识。"""
        date_key = now.strftime('%Y-%m-%d')
        if 18 <= now.hour < 20:
            return f'{date_key}:18'
        if 12 <= now.hour < 14:
            return f'{date_key}:12'
        return None

    def claim_scheduled_stamina(self, stamina_slot):
        """打开任务页，领取当前时段可领取的体力。"""
        print(f"开始执行定时体力领取: {stamina_slot}")
        self.click(2080, 650)
        print("已点击主界面右侧任务按钮")
        self.delay(2)
        self.get_screenshot('pic')

        path = os.path.dirname(__file__) + '/pic/screenshot.png'
        img = Image.open(path)
        title = self._ocr_region(img, (250, 0, 650, 120))
        if "任务" not in title:
            print("未识别到任务页，下一次十分钟巡检时重试体力领取")
            return False

        # 限定在任务行右侧区域，避免误点顶部“一键领取”。
        claim_buttons = self._find_ocr_text_centers(
            img, (1450, 280, 1800, 750), "领取"
        )
        if claim_buttons:
            for button_position in sorted(claim_buttons, key=lambda position: position[1]):
                self.click(*button_position)
                print(f"已点击体力领取按钮{button_position}")
                self.delay(1)
                self._confirm_stamina_reward()
        else:
            print("任务页当前没有可领取的体力")

        self.click(2070, 50)
        print("已关闭任务窗口")
        self.delay(1)
        return True

    def _confirm_stamina_reward(self):
        """领取体力成功后确认奖励弹窗，再由调用方关闭任务窗口。"""
        self.get_screenshot('pic')
        path = os.path.dirname(__file__) + '/pic/screenshot.png'
        img = Image.open(path)
        confirm_buttons = self._find_ocr_text_centers(
            img, (850, 750, 1550, 1030), "确定"
        )
        if not confirm_buttons:
            print("领取后未识别到奖励确认弹窗")
            return False

        self.click(*confirm_buttons[0])
        print(f"已点击奖励弹窗确定按钮{confirm_buttons[0]}")
        self.delay(0.5)
        return True

    def _find_pvp_center(self, img):
        """在当前地图截图中返回“对战中心”文字的实际中心坐标。"""
        centers = self._find_ocr_text_centers(
            img, (200, 180, 2200, 850), "对战中心"
        )
        return centers[0] if centers else None

    def enter_pvp_center(self, max_swipes=10):
        """在世界地图中滑动搜索并进入PVP对战中心。"""
        path = os.path.dirname(__file__) + '/pic/screenshot.png'

        # 如果已经在玩家对战中心，不再滑动或重复点击。
        self.get_screenshot('pic')
        current_img = Image.open(path)
        current_page_text = self._ocr_region(current_img, (700, 0, 1700, 150))
        if "在线匹配" in current_page_text or "玩家对战中心" in current_page_text:
            print("当前已在PVP对战中心")
            return True

        # 长距离快速右划，先将地图归位到最左侧。
        self.swipe_custom(300, 600, 2100, 600, 100)
        print("已快速右划地图，尝试归位到最左侧")
        self.delay(1)

        for scan_index in range(max_swipes + 1):
            self.get_screenshot('pic')
            img = Image.open(path)
            pvp_position = self._find_pvp_center(img)
            if pvp_position:
                self.click(*pvp_position)
                print(f"识别到PVP对战中心{pvp_position}，已点击进入")
                self.delay(3)
                return True

            if scan_index == max_swipes:
                break

            # 按实测有效坐标每次滑动200像素，移动后重新截图做非固定位置OCR。
            self.swipe_custom(1100, 460, 900, 460, 800)
            print(f"未发现对战中心，第{scan_index + 1}次从(1100,460)滑动到(900,460)")
            self.delay(1)

        print(f"连续扫描{max_swipes + 1}个地图位置，未识别到PVP对战中心")
        return False

    def prepare_scheduled_pvp(self):
        """进入PVP页、选择右侧编队并确认，为纯人机自动PVP做好准备。"""
        if not self.enter_pvp_center():
            return False

        path = os.path.dirname(__file__) + '/pic/screenshot.png'

        # 进入对战中心建筑后，按约定坐标打开玩家PVP入口。
        self.click(945, 520)
        print("已点击对战中心内的PVP入口(945, 520)")
        self.delay(2)
        self.get_screenshot('pic')
        pvp_img = Image.open(path)
        pvp_title = self._ocr_region(pvp_img, (700, 0, 1700, 150))
        if "玩家对战中心" not in pvp_title:
            print("未识别到玩家对战中心页面，下一次十分钟巡检时重试")
            return False

        lineup_buttons = self._find_ocr_text_centers(
            pvp_img, (500, 500, 1000, 850), "调整阵容"
        )
        if not lineup_buttons:
            print("玩家对战中心页面未识别到“调整阵容”按钮")
            return False
        self.click(*lineup_buttons[0])
        print(f"已点击调整阵容{lineup_buttons[0]}")
        self.delay(2)

        self.get_screenshot('pic')
        lineup_img = Image.open(path)
        lineup_title = self._ocr_region(lineup_img, (700, 0, 1700, 160))
        if "出战精灵" not in lineup_title:
            print("未识别到出战精灵编队页面")
            return False

        # 先确认编队窗口和“确定”按钮已完整显示，再操作编队位置。
        confirm_buttons = self._find_ocr_text_centers(
            lineup_img, (1750, 150, 2200, 350), "确定"
        )
        if not confirm_buttons:
            print("等待2秒后仍未识别到“确定”按钮，不点击编队")
            return False

        # 编队名称可能被用户修改，直接点击右侧确定按钮下方的编队按钮。
        team_position = (1939, 440)
        self.click(*team_position)
        print(f"已点击右侧编队按钮{team_position}")
        self.delay(1)

        # 编队按钮不会改变确认按钮位置，点击此前已确认出现的按钮。
        self.click(*confirm_buttons[0])
        print(f"已确认出战编队{confirm_buttons[0]}")
        self.delay(2)
        return True

    def _find_next_sign_reward(self, img):
        """根据绿色对勾找到按行排列的第一个未领取签到奖励。"""
        img_rgb = np.array(img.convert('RGB'))
        hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
        green_mask = cv2.inRange(
            hsv, np.array([35, 120, 100]), np.array([85, 255, 255])
        )

        # 只分析奖励格区域，排除页面其他绿色装饰。
        reward_mask = np.zeros_like(green_mask)
        reward_mask[250:1030, 600:1550] = green_mask[250:1030, 600:1550]
        component_count, _, stats, centers = cv2.connectedComponentsWithStats(
            reward_mask
        )

        claimed_centers = []
        for index in range(1, component_count):
            x, y, width, height, area = stats[index]
            # 已领取对勾在当前分辨率约为60x47；排除绿色道具本身。
            if (45 <= width <= 75 and 35 <= height <= 65
                    and 500 <= area <= 1300):
                claimed_centers.append(
                    (int(centers[index][0]), int(centers[index][1]))
                )

        column_centers = (756, 933, 1111, 1288, 1465)
        if not claimed_centers:
            # 月初尚无任何已领取格时，领取左上角第一个奖励。
            return 756, 440

        last_claimed = max(claimed_centers, key=lambda position: (position[1], position[0]))
        column_index = min(
            range(len(column_centers)),
            key=lambda index: abs(column_centers[index] - last_claimed[0])
        )
        if column_index < len(column_centers) - 1:
            return column_centers[column_index + 1], last_claimed[1]
        return column_centers[0], last_claimed[1] + 177

    def check_sign_reward(self):
        """领取每日签到奖励，随后在福利窗口中执行在线奖励抽奖。"""
        print("检查签到奖励...")
        self.get_screenshot('pic')
        path = os.path.dirname(__file__) + '/pic/screenshot.png'
        img = Image.open(path)
        sign_text = self._ocr_region(img, (650, 90, 1450, 330))
        if "签到奖励" not in sign_text:
            print("无签到奖励窗口")
            return False

        if "今日已签到" in sign_text:
            print("今日签到奖励已经领取，继续处理在线奖励")
        elif "今日未签到" not in sign_text:
            print(f"签到状态识别不明确，不执行领取: {sign_text}")
            return False
        else:
            reward_position = self._find_next_sign_reward(img)
            self.click(*reward_position)
            print(f"已点击第一个未领取的签到奖励{reward_position}")
            self.delay(2)

            self.get_screenshot('pic')
            reward_img = Image.open(path)
            confirm_buttons = self._find_ocr_text_centers(
                reward_img, (850, 750, 1550, 1030), "确定"
            )
            if not confirm_buttons:
                print("点击签到奖励后未识别到“确定”按钮")
                return False

            self.click(*confirm_buttons[0])
            print(f"已点击签到奖励确定按钮{confirm_buttons[0]}")
            self.delay(2)

        return self.collect_online_rewards()

    def _is_online_energy_complete(self, text):
        """容错识别在线奖励的能量收集完成文案。"""
        normalized_text = re.sub(r'[\s，。！？、,.!~～]+', '', text or '')
        completion_phrases = (
            "能量已经收集完",
            "能量已收集完",
            "能量已经收集完成",
            "能量收集完成",
        )
        if any(phrase in normalized_text for phrase in completion_phrases):
            return True

        # 允许OCR在“能量”和“收集完”之间混入少量误识别字符。
        return (
            "能量" in normalized_text
            and ("收集完" in normalized_text or "收集完成" in normalized_text)
        )

    def collect_online_rewards(self):
        """切换到在线奖励，等待一小时后完成四次转盘抽奖。"""
        path = os.path.dirname(__file__) + '/pic/screenshot.png'
        self.get_screenshot('pic')
        benefits_img = Image.open(path)
        online_tabs = self._find_ocr_text_centers(
            benefits_img, (250, 400, 650, 800), "在线奖励"
        )
        if not online_tabs:
            print("福利窗口中未识别到“在线奖励”标签")
            self.click(2070, 50)
            self.delay(1)
            return False

        self.click(*online_tabs[0])
        print(f"已切换到在线奖励{online_tabs[0]}")
        self.delay(2)
        self.get_screenshot('pic')
        online_img = Image.open(path)
        online_text = self._ocr_region(online_img, (650, 100, 2100, 900))
        if "能量站" not in online_text and "能量转盘" not in online_text:
            print("未识别到在线奖励转盘页面，关闭福利窗口")
            self.click(2070, 50)
            self.delay(1)
            return False

        print("在线奖励页面已打开，等待1小时后开始4次抽奖...")
        self.delay(3600)

        wheel_center = (985, 560)
        completed_draws = 0
        energy_collection_complete = False
        for draw_index in range(4):
            self.click(*wheel_center)
            print(f"已点击转盘中心，开始第{draw_index + 1}次抽奖")
            self.delay(2)
            self.get_screenshot('pic')
            reward_img = Image.open(path)
            confirm_buttons = self._find_ocr_text_centers(
                reward_img, (850, 750, 1550, 1030), "确定"
            )
            if not confirm_buttons:
                print(f"第{draw_index + 1}次抽奖未识别到奖品确定按钮，停止继续抽奖")
                break

            self.click(*confirm_buttons[0])
            completed_draws += 1
            print(f"第{draw_index + 1}次抽奖完成，已点击确定{confirm_buttons[0]}")
            self.delay(2)

            # 每次抽奖完成后都检查剩余次数，兼容当天此前已经抽过的情况。
            self.get_screenshot('pic')
            completed_img = Image.open(path)
            completed_text = self._ocr_region(
                completed_img, (650, 850, 1350, 1030)
            )
            if self._is_online_energy_complete(completed_text):
                energy_collection_complete = True
                print("识别到今天的能量已经收集完，停止继续抽奖")
                break

        if energy_collection_complete:
            self.click(2070, 50)
            print("已关闭福利窗口")
            self.delay(1)
            return True

        if completed_draws != 4:
            print(f"在线奖励只完成{completed_draws}/4次，暂不关闭福利窗口")
            return False

        # 第4次已经检查过一次；若文案显示较慢，再额外重试两次。
        for check_index in range(2):
            self.delay(2)
            self.get_screenshot('pic')
            completed_img = Image.open(path)
            completed_text = self._ocr_region(
                completed_img, (650, 850, 1350, 1030)
            )
            if self._is_online_energy_complete(completed_text):
                self.click(2070, 50)
                print("识别到今天的能量已经收集完，已关闭福利窗口")
                self.delay(1)
                return True
            if check_index == 0:
                print("暂未识别到能量收集完成文案，等待2秒后重试")

        print("4次抽奖已确认，但未识别到能量收集完成文案，暂不关闭福利窗口")
        return False

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
