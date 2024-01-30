import cv2
import sys
import numpy as np
import os
import os.path as op
import functools
import time
import csv
import re
import datetime
from threading import Thread, Event
from ctypes import *
import win32api
from win32api import EnumDisplayMonitors
import win32con

import matplotlib.colors as mcolors
from matplotlib.colors import ListedColormap 
from matplotlib.figure import Figure
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvas, NavigationToolbar2QT 
from sklearn.neighbors import KDTree
from scipy.interpolate import interp2d
import matplotlib.pyplot as plt

import vtk
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor# 三维显示
# noinspection PyUnresolvedReferences
import vtkmodules.vtkInteractionStyle
# noinspection PyUnresolvedReferences
import vtkmodules.vtkRenderingOpenGL2
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

from threading import Thread
import pyqtgraph.opengl as gl
from pyqtgraph import PlotWidget
from pyqtgraph import Vector

from utils.generate_config import My_Config
import gxipy as gx
from utils.camera import My_Camera
from utils.base import resize_for_show_win
from utils.artDaq import artDaq
import open3d as o3d

from UI.ui_DMD import Ui_MainWindow
from qfluentwidgets import (PushButton, TeachingTip, TeachingTipTailPosition, InfoBarIcon, setTheme, Theme,TeachingTipView, FlyoutViewBase, BodyLabel, PrimaryPushButton, PopupTeachingTip, PillPushButton, Slider, ComboBox, DoubleSpinBox, SpinBox, InfoBar, InfoBarPosition, StateToolTip)
from qfluentwidgets import FluentIcon as FIF
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import QObject, QTimer, QRect, QSize, Qt, QPointF, QPropertyAnimation, QParallelAnimationGroup, QEasingCurve, QMargins, Signal
from PySide6.QtWidgets import QMainWindow, QApplication, QGroupBox, QStyle, QPushButton, QWidget, QMenu, QLabel, QDial, QSizePolicy, QSlider, QGridLayout, QHBoxLayout,QVBoxLayout, QFormLayout, QFileDialog, QTableWidgetItem
from PySide6.QtGui import QImage, QPixmap, QFont, QAction, QMouseEvent, QIcon, QPalette, QBrush, QColor
from PySide6.QtCharts import QChartView, QChart, QValueAxis, QLineSeries

# 定义结构
class MyStruct(Structure):
    _fields_ = [
        ("numbegin", c_int),
        ("numend", c_int),
        ("voltageperlayer", c_double),
        ("fun1", CFUNCTYPE(None)),
        ("fun2", CFUNCTYPE(None)),
        ("data", c_double * 2),
    ]


# 主界面
class MainWindow(QMainWindow):
    '''
    主界面的类
    '''
    def __init__(self):
        '''
        初始化主界面
        '''
        super().__init__()

        # 加载UI
        self.ui = Ui_MainWindow() # 实例化UI对象
        self.ui.setupUi(self) # 初始化

        # 模式选择设置
        items = ['24Hz', '60Hz']
        self.ui.ComboBox_choose_frequency.addItems(items)
        self.ui.ComboBox_choose_frequency.setCurrentIndex(-1)
        self.ui.ComboBox_choose_frequency.currentTextChanged.connect(functools.partial(self.ComboBox_textchange, 'ComboBox_choose_frequency'))

        items = ['横线线列', '竖线线列', '点阵阵列']
        self.ui.ComboBox_patten_choose.addItems(items)
        self.ui.ComboBox_patten_choose.setCurrentIndex(-1)
        self.ui.ComboBox_patten_choose.currentTextChanged.connect(functools.partial(self.ComboBox_textchange, 'ComboBox_patten_choose'))

        items = ['新生成掩膜', '读取已有掩膜']
        self.ui.ComboBox_choose_mask.addItems(items)
        self.ui.ComboBox_choose_mask.setCurrentIndex(-1)
        self.ui.ComboBox_choose_mask.currentTextChanged.connect(functools.partial(self.ComboBox_textchange, 'ComboBox_choose_mask'))

        items = ['做差法', '预先法']
        self.ui.ComboBox_generate_mask_method.addItems(items)
        self.ui.ComboBox_generate_mask_method.setCurrentIndex(-1)
        self.ui.ComboBox_generate_mask_method.currentTextChanged.connect(functools.partial(self.ComboBox_textchange, 'ComboBox_generate_mask_method'))

        items = ['极值法', '质心法', '高斯法']
        self.ui.ComboBox_tomography_method.addItems(items)
        self.ui.ComboBox_tomography_method.setCurrentIndex(-1)
        self.ui.ComboBox_tomography_method.currentTextChanged.connect(functools.partial(self.ComboBox_textchange, 'ComboBox_tomography_method'))

        items = ['不插值', '一次插值', '三次插值']
        self.ui.ComboBox_interpolation_method.addItems(items)
        self.ui.ComboBox_interpolation_method.setCurrentIndex(-1)
        self.ui.ComboBox_interpolation_method.currentTextChanged.connect(functools.partial(self.ComboBox_textchange, 'ComboBox_interpolation_method'))

        # 输入框管理
        self.ui.SpinBox_per_frame.valueChanged.connect(functools.partial(self.upgrate_value, 'SpinBox_per_frame'))
        self.ui.DoubleSpinBox_pzt_move_time.valueChanged.connect(functools.partial(self.upgrate_value, 'DoubleSpinBox_pzt_move_time'))
        self.ui.DoubleSpinBox_pre_expo.valueChanged.connect(functools.partial(self.upgrate_value, 'DoubleSpinBox_pre_expo'))
        self.ui.DoubleSpinBox_expo.valueChanged.connect(functools.partial(self.upgrate_value, 'DoubleSpinBox_expo'))
        self.ui.DoubleSpinBox_post_expo.valueChanged.connect(functools.partial(self.upgrate_value, 'DoubleSpinBox_post_expo'))
        self.ui.SpinBox_patten_width.valueChanged.connect(functools.partial(self.upgrate_value, 'SpinBox_patten_width'))
        self.ui.SpinBox_patten_T.valueChanged.connect(functools.partial(self.upgrate_value, 'SpinBox_patten_T'))
        self.ui.SpinBox_patten_num.valueChanged.connect(functools.partial(self.upgrate_value, 'SpinBox_patten_num'))
        self.ui.SpinBox_patten_index.valueChanged.connect(functools.partial(self.upgrate_value, 'SpinBox_patten_index'))
        self.ui.SpinBox_patten_x_coordinate.valueChanged.connect(functools.partial(self.upgrate_value, 'SpinBox_patten_x_coordinate'))
        self.ui.SpinBox_patten_y_coordinate.valueChanged.connect(functools.partial(self.upgrate_value, 'SpinBox_patten_y_coordinate'))
        self.ui.doubleSpinBox_camera_expos.valueChanged.connect(functools.partial(self.upgrate_value, 'doubleSpinBox_camera_expos'))
        self.ui.DoubleSpinBox_light_strength.valueChanged.connect(functools.partial(self.upgrate_value, 'DoubleSpinBox_light_strength'))
        self.ui.SpinBox_scan_layer_num.valueChanged.connect(functools.partial(self.upgrate_value, 'SpinBox_scan_layer_num'))
        self.ui.DoubleSpinBox_pzt_location.valueChanged.connect(functools.partial(self.upgrate_value, 'DoubleSpinBox_pzt_location'))
        self.ui.DoubleSpinBox_scan_step.valueChanged.connect(functools.partial(self.upgrate_value, 'DoubleSpinBox_scan_step'))
        self.ui.DoubleSpinBox_scaning_step.valueChanged.connect(functools.partial(self.upgrate_value, 'DoubleSpinBox_scaning_step'))
        self.ui.DoubleSpinBox_scale_index.valueChanged.connect(functools.partial(self.upgrate_value, 'DoubleSpinBox_scale_index'))
        
        # 按钮管理
        self.ui.PushButton_DMD_set.clicked.connect(self.setexternalpattern)
        self.ui.PushButton_DMD_confirm.clicked.connect(self.changeDMDfps)
        self.ui.PushButton_patten_confirm.clicked.connect(self.generate_patten)
        self.ui.PushButton_camera_set.clicked.connect(self.camera_init)
        self.ui.PushButton_camera_work.clicked.connect(self.camera_work)
        self.ui.PushButton_camera_save.clicked.connect(self.camera_img_save)
        self.ui.PushButton_mask_parm_set.clicked.connect(self.mask_para_set)
        self.ui.PushButton_camera_more_parm.clicked.connect(self.camera_parm_set)
        self.ui.PushButton_scaning_init.clicked.connect(self.scan_init)
        self.ui.PushButton_scaning.clicked.connect(self.begintomeasure)
        self.ui.PushButton_save_npy.clicked.connect(self.save_data_npy)
        self.ui.PushButton_browse_images.clicked.connect(self.browse_images)
        self.ui.PushButton_show_axial_envelope.clicked.connect(self.show_axial_envelope)
        self.ui.PushButton_show_section_line.clicked.connect(self.show_section_line)
        self.ui.PushButton_generate_tomography_3d.clicked.connect(self.generate_tomography)
        self.ui.PushButton_save_pointcloud.clicked.connect(self.save_ply)
        self.ui.PushButton_show_mesh.clicked.connect(self.show_mesh)
        self.ui.SwitchButton_incline_calibration.checkedChanged.connect(self.incline_calibration)
        self.ui.SwitchButton_remove_bur.checkedChanged.connect(self.remove_bur)

        # 图表管理
        self.Chartwidget_init(self.ui.widget_show_DMD_curve)
        self.Chartwidget_init(self.ui.widget_patten_set)
        self.Chartwidget_init(self.ui.widget_axial_envelope)

        # 界面切换管理
        self.ui.SegmentedWidget_total.addItem("handware_set", "硬件参数设置", lambda: self.ui.stackedWidget_total.setCurrentIndex(0))
        self.ui.SegmentedWidget_total.addItem("softset", "软件显示", lambda: self.ui.stackedWidget_total.setCurrentIndex(1))

        self.ui.SegmentedWidget.addItem("show_images", "浏览图片", lambda: self.ui.stackedWidget_show_view.setCurrentIndex(0))
        self.ui.SegmentedWidget.addItem("show_mask_area", "显示掩膜区域", lambda: self.ui.stackedWidget_show_view.setCurrentIndex(1))
        self.ui.SegmentedWidget.addItem("show_2d_image", "显示二维图像", lambda: self.ui.stackedWidget_show_view.setCurrentIndex(2))
        self.ui.SegmentedWidget.addItem("show_3d_pointcloud", "显示三维点云", lambda: self.ui.stackedWidget_show_view.setCurrentIndex(3))
        self.ui.SegmentedWidget.addItem("show_mesh", "显示多边形", lambda: self.ui.stackedWidget_show_view.setCurrentIndex(4))

        # 文件加载区的设置
        self.ui.SearchLineEdit_npypath.searchButton.clicked.connect(functools.partial(self.Select_existing_folder, 'SearchLineEdit_npypath'))
        self.ui.SearchLineEdit_maskpath.searchButton.clicked.connect(functools.partial(self.Select_existing_folder, 'SearchLineEdit_maskpath'))        
        self.ui.SearchLineEdit_imgmask_path.searchButton.clicked.connect(functools.partial(self.Select_existing_folder, 'SearchLineEdit_imgmask_path'))

        # 提示小控件设置
        self.mainprocess_stateTooltip = None

        # 初始化各模块
        self.init()
    

    def init(self):
        
        # 读取配置文件
        print('读取配置文件', end='')
        self.Config = My_Config()
        self.Config.read()
        print('\r配置文件读取完毕')

        # 初始化参数设置
        self.pzt_move_time = self.Config.config['DMD设置']['预留PZT移动时间']
        self.ui.DoubleSpinBox_pzt_move_time.setValue(self.pzt_move_time)
        self.choose_frequency = self.Config.config['DMD设置']['DMD读取帧率设置']
        self.DMD_frequency = self.Config.config['DMD设置']['DMD读取帧率']
        self.ui.ComboBox_choose_frequency.setText(self.choose_frequency)
        self.ComboBox_textchange(self, "ComboBox_choose_frequency")
        self.DMD_per_frame = self.Config.config['DMD设置']['显示图样数']
        self.ui.SpinBox_per_frame.setValue(self.DMD_per_frame)
        self.calculate_DMD_parameter()
        self.Update_chartwidget(self.ui.widget_show_DMD_curve, 0, 0)


        self.patten_choose = self.Config.config['图案设置']['图案模式选择']
        self.ui.ComboBox_patten_choose.setText(self.patten_choose)
        self.patten_width = self.Config.config['图案设置']['图案宽度']
        self.ui.SpinBox_patten_width.setValue(self.patten_width)
        self.patten_T = self.Config.config['图案设置']['图案周期']
        self.ui.SpinBox_patten_T.setValue(self.patten_T)
        self.patten_num = self.Config.config['图案设置']['图案数量']
        self.ui.SpinBox_patten_num.setValue(self.patten_num)
        self.patten_index = self.Config.config['图案设置']['图案编号']
        self.ui.SpinBox_patten_index.setValue(self.patten_index)
        self.patten_x_coordinate = self.Config.config['图案设置']['图案x坐标']
        self.ui.SpinBox_patten_x_coordinate.setValue(self.patten_x_coordinate)
        self.patten_y_coordinate = self.Config.config['图案设置']['图案y坐标']
        self.ui.SpinBox_patten_y_coordinate.setValue(self.patten_y_coordinate)

        self.camera_expos = self.Config.config['相机设置']['相机曝光时间']
        self.ui.doubleSpinBox_camera_expos.setValue(self.camera_expos)
        self.camera_frame = self.Config.config['相机设置']['相机帧率']
        self.camera_gain = self.Config.config['相机设置']['相机增益']
        self.camera_ROIx = self.Config.config['相机设置']['ROI原点x坐标']
        self.camera_ROIy = self.Config.config['相机设置']['ROI原点y坐标']
        self.camera_ROIw = self.Config.config['相机设置']['ROI宽度']
        self.camera_ROIh = self.Config.config['相机设置']['ROI高度']

        self.light_strength = self.Config.config['采集设置']['光源强度']
        self.ui.DoubleSpinBox_light_strength.setValue(self.light_strength)
        self.scan_layer_num = self.Config.config['采集设置']['扫描层数']
        self.ui.SpinBox_scan_layer_num.setValue(self.scan_layer_num)
        self.pzt_location = self.Config.config['采集设置']['pzt位置']
        self.ui.DoubleSpinBox_pzt_location.setValue(self.pzt_location)
        self.scan_step = self.Config.config['采集设置']['扫描步进']
        self.ui.DoubleSpinBox_scan_step.setValue(self.scan_step)

        self.origin_npypath = self.Config.config['文件选择区']['图片文件夹']
        self.Maskpath = self.Config.config['文件选择区']['掩膜文件']
        self.Maskimgpath = self.Config.config['文件选择区']['平面照明光斑图']

        self.choose_mask = self.Config.config['模式选择区']['掩膜导入']
        self.ui.ComboBox_choose_mask.setText(self.choose_mask)
        self.mask_num = self.Config.config['模式选择区']['掩膜图片数量']
        self.maskimg_index = self.Config.config['模式选择区']['掩膜图片编号']
        self.generate_mask_method = self.Config.config['模式选择区']['掩膜生成方法']
        self.ui.ComboBox_generate_mask_method.setText(self.generate_mask_method)
        self.threshold_method = self.Config.config['模式选择区']['阈值分割方法']
        self.threshold_value = self.Config.config['模式选择区']['设定阈值']
        self.image_group = self.Config.config['模式选择区']['浏览图片组序']
        self.image_browse_index = self.Config.config['模式选择区']['浏览图片图序']

        self.tomography_method = self.Config.config['三维形貌生成']['轴向包络提取方法']
        self.ui.ComboBox_tomography_method.setText(self.tomography_method)
        self.scaning_step = self.Config.config['三维形貌生成']['扫描步进']
        self.ui.DoubleSpinBox_scaning_step.setValue(self.scaning_step)
        self.scale_index = self.Config.config['三维形貌生成']['缩放系数']
        self.ui.DoubleSpinBox_scale_index.setValue(self.scale_index)
        self.interpolation_method = self.Config.config['三维形貌生成']['插值方法']
        self.ui.ComboBox_tomography_method.setText(self.interpolation_method)

        self.camera_scaled_index = self.Config.config["视场大小"]['放大倍数']
        self.camera_uint_size = self.Config.config['视场大小']['相机像元尺寸']

        # DMD初始化
        # 控制dmd的dll
        self.dll_ControlDMD = cdll.LoadLibrary(r"c_dll/DMD_DLLL/Dll_ControlDMD.dll")
        # 设置控制dmd函数的参数类型
        self.dll_ControlDMD.ConnectionAndInitial.argtypes = None
        self.dll_ControlDMD.ConnectionAndInitial.restype = c_bool
        self.dll_ControlDMD.DisplayExternalPatternStreaming.argtypes = [
            c_ubyte,  # unsigned char numberofpattern
            c_uint,   # unsigned int preilluminationdarktime
            c_uint,   # unsigned int illuminationtime
            c_uint    # unsigned int Postilluminationdarktime
        ]
        self.dll_ControlDMD.DisplayExternalPatternStreaming.restype = None
        # 初始化与DMD的连接
        self.DMD_Status =  self.dll_ControlDMD.ConnectionAndInitial()

        # 初始化屏幕
        # 获取显示器的设备名称
        self.device_name = None
        devices = []
        index = 0
        while True:
            try:
                device = win32api.EnumDisplayDevices(None, index)
                devices.append(device)
                index += 1
            except:
                break
        try:
            # 获取第二个显示器的设备名称
            self.device_name = devices[1].DeviceName
            # 获取当前显示设置
            self.current_settings = win32api.EnumDisplaySettings(self.device_name, win32con.ENUM_CURRENT_SETTINGS)
        except:
            print("donot find the second screen #$#")

        # 初始化相机
        self.camera_init()

        # 初始化数采卡
        # 设置控制DAQ函数的参数类型
        self.dll_DAQ = cdll.LoadLibrary(r"c_dll\DAQ_dll\Dll1.dll")
        self.dll_DAQ.DAQcontrol.argtypes = [ c_double, POINTER(MyStruct)]
        self.dll_DAQ.DAQcontrol.restype = None
        self.dll_DAQ.StartDAQtask.argtypes = None
        self.dll_DAQ.StartDAQtask.restype = None
        # 初始化pzt控制
        self.Daq = artDaq('4369')
        self.Daq.init_daq()
        self.Daq.set_pzt_channel('Dev1/ao1') 

        # 三维扫描初始化
        self.scaning_flag = False
        self.incline_calibration_status = False
        self.remove_bur_status = False
        
        print("------------")

        # 多线程设置
        # 线程1 并行数据三维形貌生成
        self.thread1 = Thread(target=self.generate_multithread)
        self.thread1_endevent = False


######################################################
# UI功能区

    def Chartwidget_init(self, target):
        """
        对chart进行初始化设置
        """
        if target == self.ui.widget_show_DMD_curve:
            # self.ui.widget_show_DMD_curve.resize(600, 290)
            self.ui.widget_show_DMD_curve.option = {
                "xAxis": {
                    "name": "时间"
                },
                "yAxis": {},
                "tooltip":{"show":True, 'formatter': "{c}",},
                "dataZoom": [
                    {
                    "type": 'slider',
                    "xAxisIndex": 0,
                    "filterMode": 'none'
                    },
                    {
                    "type": 'slider',
                    "yAxisIndex": 0,
                    "filterMode": 'none'
                    },
                ],
                "series": [
                    {
                    "data": [],
                    "type": 'line',
                    'lineStyle': {
                        'width': 4
                    }
                    },
                    {
                    "data": [],
                    "type": 'line',
                    "areaStyle": {},
                    'lineStyle': {
                        'width': 4
                    }
                    }
                ]
                }
            self.ui.widget_show_DMD_curve.option["series"][0]["data"] = [[0,0],[0,1],[1.04,1],[1.04,0],[41.66,0],[41.66,1],[42.7,1],[42.7,0],[50,0]]
            self.ui.widget_show_DMD_curve.option["series"][1]["data"] = [[i, 0] for i in range(51)]
            self.ui.widget_show_DMD_curve.setChart(Chart(InitOpts(height="350px", width="650px", is_horizontal_center=True)))
            self.ui.widget_show_DMD_curve.setChartOptions(self.ui.widget_show_DMD_curve.option)

        elif target == self.ui.widget_patten_set:
            self.ui.widget_patten_set.option = {
            "visualMap": [{
                    "show": False,
                    "min": 0,
                    "max": 3,
                    'inRange': {
                        'color': ['blue','green','yellow','red'],}
                }],
            "tooltip":{"show":False, 'formatter': "{c}",},
            "xAxis": {
                "min": 0,
                "max": 4,
                "type": 'value',
                "axisLine": { "onZero": "false" },
                'interval': 1,
                "splitLine": {'show': 'true',
                              'interval': 1,
                              'lineStyle': {'width': 3, 'color': 'black'} },                       
            },
            "yAxis": {
                "min": 0,
                "max": 4,
                "type": 'value',
                'interval': 1,
                'inverse': 'true',
                "axisLine": { "onZero": "false" },
                "splitLine": {'show': 'true',
                              'interval': 1,
                              'lineStyle': {'width': 3, 'color': 'black'} }
            },
            "series": [
                {
                "id": 'a',
                "type": 'line',
                "smooth": "true",
                "symbolSize": 20,
                "data": [[2,3],[1,1],[4,2.5]],
                'label':{'show': True, 'position': "inside", 'formatter': "{@[2]}", "fontWeight":"bolder", 'fontSize': 15}
                }
            ],
            }
            self.ui.widget_patten_set.setChart(Chart(InitOpts(height="350px", width="300px", is_horizontal_center=True)))
            self.ui.widget_patten_set.setChartOptions(self.ui.widget_patten_set.option)
        
        elif target == self.ui.widget_axial_envelope:
            
            self.ui.widget_axial_envelope.option = {
                "xAxis": {
                    "name": "轴向高度（微米）",
                    'nameLocation': 'center', 
                    'nameGap':35
                },
                "yAxis": {},
                "tooltip":{"show":True, 'formatter': "{c}",},
                "dataZoom": [
                    {
                    "type": 'slider',
                    "xAxisIndex": 0,
                    "filterMode": 'none'
                    },
                    {
                    "type": 'slider',
                    "yAxisIndex": 0,
                    "filterMode": 'none'
                    },
                ],
                "series": [
                    {
                    "data": [],
                    "type": 'line',
                    'lineStyle': {
                        'width': 4
                    }
                    },
                    
                ]
                }
            self.ui.widget_axial_envelope.option["series"][0]["data"] = [[i, 0] for i in range(51)]
            self.ui.widget_axial_envelope.setChart(Chart(InitOpts(height="300px", width="550px", is_horizontal_center=True)))
            self.ui.widget_axial_envelope.setChartOptions(self.ui.widget_axial_envelope.option)
    

    def Update_chartwidget(self, target, index=0, mode = ""):
        """
        更新图表
        """
        if target == self.ui.widget_show_DMD_curve:
            if mode == 24:
                _list = [[0,0],[0,1],[1.04,1],[1.04,0],[41.66,0],[41.66,1],[42.7,1],[42.7,0],[50,0]]
                self.ui.widget_show_DMD_curve.option["series"][index]["data"] = _list

                _list1 = self.DMD_curve_show()
                self.ui.widget_show_DMD_curve.option["series"][1]["data"] = _list1

                self.ui.widget_show_DMD_curve.updateChartOptions(self.ui.widget_show_DMD_curve.option)

            elif mode == 60:
                _list = [[0,0],[0,1],[0.4,1],[0.4,0],[16.66,0],[16.66,1],[17.06,1],[17.06,0],[20,0]]
                self.ui.widget_show_DMD_curve.option["series"][index]["data"] = _list

                _list1 = self.DMD_curve_show()
                self.ui.widget_show_DMD_curve.option["series"][1]["data"] = _list1

                self.ui.widget_show_DMD_curve.updateChartOptions(self.ui.widget_show_DMD_curve.option)
            
            elif mode == 0:
                _list1 = self.DMD_curve_show()
                self.ui.widget_show_DMD_curve.option["series"][1]["data"] = _list1

                self.ui.widget_show_DMD_curve.updateChartOptions(self.ui.widget_show_DMD_curve.option)
        
        elif target == self.ui.widget_patten_set:

            if mode == '点阵阵列':
                self.ui.widget_patten_set.option['xAxis']['max'] = self.patten_T
                self.ui.widget_patten_set.option['yAxis']['max'] = self.patten_T
                self.ui.widget_patten_set.updateChartOptions(self.ui.widget_patten_set.option)

            elif mode == '横线线列':
                self.ui.widget_patten_set.option['xAxis']['max'] = 1
                self.ui.widget_patten_set.option['yAxis']['max'] = self.patten_T
                self.ui.widget_patten_set.updateChartOptions(self.ui.widget_patten_set.option)

            elif mode == '竖线线列':
                self.ui.widget_patten_set.option['xAxis']['max'] = self.patten_T
                self.ui.widget_patten_set.option['yAxis']['max'] = 1
                self.ui.widget_patten_set.updateChartOptions(self.ui.widget_patten_set.option)
        
        elif target == self.ui.widget_axial_envelope:

            if mode == 'axial_envelope':

                self.ui.widget_axial_envelope.option['xAxis']['name'] = "轴向高度（微米）"
                if index == 0:
                    # 这是原始数据的包络
                    line = self.origin_data[self.image_group-1, :, int(self.image_x_coordinate), int(self.image_y_coordinate)]
                    x = self.scaning_step*np.arange(len(line))

                    # 使用 numpy.concatenate() 函数合并数组
                    points = np.concatenate((x.reshape(-1, 1), line.reshape(-1, 1)), axis=1)

                    # 将数组转换为列表
                    list_points = points.tolist()
                    self.ui.widget_axial_envelope.option['series'][0]['data'] = list_points
                    self.ui.widget_axial_envelope.updateChartOptions(self.ui.widget_axial_envelope.option)
                
                elif index == 2:
                    # 这是三维形貌的包络
                    # 确认包络来自哪一组数据
                    x_coordinate = round(self.image_x_coordinate*self.tomography_2d.shape[0]/(self.origin_data.shape[2]*self.camera_uint_size/self.camera_scaled_index))
                    y_coordinate = round(self.image_y_coordinate*self.tomography_2d.shape[1]/(self.origin_data.shape[3]*self.camera_uint_size/self.camera_scaled_index))
                    x_coordinate = int(x_coordinate)
                    y_coordinate = int(y_coordinate)
                    for group_index in range(len(self.multithread_value_list)):
                        value = self.multithread_value_list[group_index][x_coordinate, y_coordinate]
                        if value != 0:
                            break

                    # 确认包络的具体位置
                    _flatten_arr = self.multithread_value_list[group_index].flatten()
                    # 获取展平后的一维数组中非零元素的索引
                    non_zero_indices = np.nonzero(_flatten_arr)[0]

                    _shape = self.multithread_value_list[group_index].shape
                    index = y_coordinate+x_coordinate*_shape[1]  # 这个包络在一维的顺序（从1开始）
                    # 找到给定索引对应的值在非零元素中的位置
                    index = np.where(non_zero_indices == index)[0][0]
                    print('包络在一维的位置', index)

                    # 得到它的原始位置
                    _flatten_arr = self.multithread_value_nan_list[group_index].flatten()
                    # 遍历展平后的数组，找到第n个非NaN元素及其二维索引
                    count = 0
                    for i, value in enumerate(_flatten_arr):
                        if not np.isnan(value):
                            count += 1
                            if count == index:
                                coordinate = np.unravel_index(i, self.multithread_value_nan_list[group_index].shape)
                                break
                    print('实际坐标', coordinate)
                    
                    line = self.origin_data[group_index, :, int(coordinate[0]), int(coordinate[1])]
                    x = self.scaning_step*np.arange(len(line))

                    # 使用 numpy.concatenate() 函数合并数组
                    points = np.concatenate((x.reshape(-1, 1), line.reshape(-1, 1)), axis=1)

                    # 将数组转换为列表
                    list_points = points.tolist()
                    self.ui.widget_axial_envelope.option['series'][0]['data'] = list_points
                    self.ui.widget_axial_envelope.updateChartOptions(self.ui.widget_axial_envelope.option)
                    print("这是三维形貌的轴向包络")

            elif mode == 'section_envelope':

                self.ui.widget_axial_envelope.option['xAxis']['name'] = "横向宽度（微米）"
                
                direction = self.choose_section_direction   # 剖线的方向
                line_coordinate = self.section_line_coordinate  # 剖线的坐标
                tomography_2d = self.tomography_2d  # 三维形貌数组
                unit = self.camera_uint_size/self.camera_scaled_index*self.origin_data.shape[2]/tomography_2d.shape[0]    # 两个数对应的实际距离(微米)

                if direction == 'x方向':
                    line_coordinate = round(line_coordinate*self.tomography_2d.shape[0]/(self.origin_data.shape[2]*self.camera_uint_size/self.camera_scaled_index))
                    line = tomography_2d[line_coordinate]
                elif direction == 'y方向':
                    line_coordinate = round(line_coordinate*self.tomography_2d.shape[1]/(self.origin_data.shape[3]*self.camera_uint_size/self.camera_scaled_index))
                    line = tomography_2d[:, line_coordinate]
                
                x = unit*np.arange(len(line))

                # 使用 numpy.concatenate() 函数合并数组
                points = np.concatenate((x.reshape(-1, 1), line.reshape(-1, 1)), axis=1)

                # 将数组转换为列表
                list_points = points.tolist()
                self.ui.widget_axial_envelope.option['series'][0]['data'] = list_points
                self.ui.widget_axial_envelope.updateChartOptions(self.ui.widget_axial_envelope.option)

    
    def ComboBox_textchange(self, target, text):
        """
        对comobox选择的值进行一个统一的管理
        """
        if target == "ComboBox_choose_frequency":
            self.choose_frequency = text
            if self.choose_frequency == "24Hz":
                self.DMD_frequency = 24
                self.calculate_DMD_parameter()
                self.Update_chartwidget(self.ui.widget_show_DMD_curve, 0, 24)
                
            elif self.choose_frequency == "60Hz":
                self.DMD_frequency = 60
                self.calculate_DMD_parameter()
                self.Update_chartwidget(self.ui.widget_show_DMD_curve, 0, 60)
            print(self.choose_frequency)
        
        elif target == 'ComboBox_patten_choose':
            self.patten_choose = text
            print(text)
            if self.patten_choose == "点阵阵列":
                self.ui.SpinBox_patten_y_coordinate.setEnabled(True)
                self.ui.widget_patten_set.option = {
                "visualMap": [{
                    "show": False,
                    "min": 0,
                    "max": self.patten_num-1,
                    'inRange': {
                        'color': ['blue','green','yellow','red'],}
                }],
                "tooltip":{"show":False},
                "xAxis": {
                    "min": 0,
                    "max": self.patten_T,
                    "type": 'value',
                    "axisLine": { "onZero": "false" },
                    'interval': 1,
                    "splitLine": {'show': 'true',
                                'interval': 1,
                                'lineStyle': {'width': 3, 'color': 'black'} },                       
                },
                "yAxis": {
                    "min": 0,
                    "max": self.patten_T,
                    "type": 'value',
                    'interval': 1,
                    'inverse': 'true',
                    "axisLine": { "onZero": "false" },
                    "splitLine": {'show': 'true',
                                'interval': 1,
                                'lineStyle': {'width': 3, 'color': 'black'} }
                },
                "series": [
                    {
                    "id": 'a',
                    "type": 'line',
                    "smooth": "true",
                    "symbolSize": 20,
                    "data": [[2,3],[1,1],[4,2.5]],
                    'label':{'show': True, 'position': "inside", 'formatter': "{@[2]}", "fontWeight":"bolder", 'fontSize': 15}
                    }
                ],
                }
                self.ui.widget_patten_set.setChartOptions(self.ui.widget_patten_set.option)
                self.generate_patten_series()

            elif self.patten_choose == "竖线线列":
                self.ui.SpinBox_patten_y_coordinate.setValue(1)
                self.ui.SpinBox_patten_y_coordinate.setEnabled(False)
                self.ui.widget_patten_set.option = {
                "visualMap": [{
                    "show": False,
                    "min": 0,
                    "max": self.patten_num-1,
                    'inRange': {
                        'color': ['blue','green','yellow','red'],}
                }],
                "tooltip":{"show":False},
                "xAxis": {
                    "min": 0,
                    "max": self.patten_T,
                    "type": 'value',
                    "axisLine": { "onZero": "false" },
                    'interval': 1,
                    "splitLine": {'show': 'true',
                                'interval': 1,
                                'lineStyle': {'width': 3, 'color': 'black'} },                       
                },
                "yAxis": {
                    "min": 0,
                    "max": 1,
                    "type": 'value',
                    'interval': 1,
                    'inverse': 'true',
                    "axisLine": { "onZero": "false" },
                    
                },
                "series": [
                    {
                    "id": 'a',
                    "type": 'line',
                    "smooth": "true",
                    "symbolSize": 20,
                    "data": [[2,3],[1,1],[4,2.5]],
                    'label':{'show': True, 'position': "inside", 'formatter': "{@[2]}", "fontWeight":"bolder", 'fontSize': 15}
                    }
                ],
                }
                self.ui.widget_patten_set.setChartOptions(self.ui.widget_patten_set.option)
                self.generate_patten_series()
            
            elif self.patten_choose == "横线线列":
                self.ui.SpinBox_patten_y_coordinate.setValue(1)
                self.ui.SpinBox_patten_y_coordinate.setEnabled(False)
                self.ui.widget_patten_set.option = {
                "visualMap": [{
                    "show": False,
                    "min": 0,
                    "max": self.patten_num-1,
                    'inRange': {
                        'color': ['blue','green','yellow','red'],}
                }],
                "tooltip":{"show":False},
                "xAxis": {
                    "min": 0,
                    "max": 1,
                    "type": 'value',
                    "axisLine": { "onZero": "false" },
                    'interval': 1,
                    "splitLine": {'show': 'false',
                                'interval': 1,
                                 },                  
                },
                "yAxis": {
                    "min": 0,
                    "max": self.patten_T,
                    "type": 'value',
                    'interval': 1,
                    'inverse': 'true',
                    "axisLine": { "onZero": "false" },
                    "splitLine": {'show': 'true',
                                'interval': 1,
                                'lineStyle': {'width': 3, 'color': 'black'} },  
                },
                "series": [
                    {
                    "id": 'a',
                    "type": 'line',
                    "smooth": "true",
                    "symbolSize": 20,
                    "data": [[2,3],[1,1],[4,2.5]],
                    'label':{'show': True, 'position': "inside", 'formatter': "{@[2]}", "fontWeight":"bolder", 'fontSize': 15}
                    }
                ],
                }
                self.ui.widget_patten_set.setChartOptions(self.ui.widget_patten_set.option)
                self.generate_patten_series()

        elif target == 'ComboBox_choose_mask':
            self.choose_mask = text
            if self.choose_mask == "新生成掩膜":
                self.ui.ComboBox_generate_mask_method.setEnabled(True)
                self.ui.SearchLineEdit_maskpath.setEnabled(False)
                self.ui.SearchLineEdit_imgmask_path.setEnabled(True)
                self.ui.PushButton_mask_parm_set.setEnabled(True)
                self.ui.PushButton_browse_images.setEnabled(True)
            elif self.choose_mask == "读取已有掩膜":
                self.ui.ComboBox_generate_mask_method.setEnabled(False)
                self.ui.SearchLineEdit_maskpath.setEnabled(True)
                self.ui.SearchLineEdit_imgmask_path.setEnabled(False)
                self.ui.PushButton_mask_parm_set.setEnabled(False)
                self.ui.PushButton_browse_images.setEnabled(False)

        elif target == 'ComboBox_generate_mask_method':
            self.generate_mask_method = text
        
        elif target == "ComboBox_threshold_method":
            self.threshold_method = text

        elif target == "ComboBox_tomography_method":
            self.tomography_method = text
            
        elif target == "ComboBox_interpolation_method":
            self.interpolation_method = text
        
        elif target == "ComboBox_choose_section_direction":
            self.choose_section_direction = text
        

    def upgrate_value(self, target, value):
        """
        对由doublespinbox与spinbox得到的数值进行一个统一管理, 对值的改变进行某些操作
        """
        if target == "SpinBox_per_frame":
            self.DMD_per_frame = value
            self.calculate_DMD_parameter()
            self.Update_chartwidget(self.ui.widget_show_DMD_curve, 0, 0)
        
        elif target == 'DoubleSpinBox_pzt_move_time':
            self.pzt_move_time = value
            self.calculate_DMD_parameter()

        elif target == "DoubleSpinBox_pre_expo":
            self.DMD_pre_expo = value
            self.Update_chartwidget(self.ui.widget_show_DMD_curve, 0, 0)

        elif target == "DoubleSpinBox_expo":
            self.DMD_expo = value
            self.Update_chartwidget(self.ui.widget_show_DMD_curve, 0, 0)

        elif target == "DoubleSpinBox_post_expo":
            self.DMD_post_expo = value
            self.Update_chartwidget(self.ui.widget_show_DMD_curve, 0, 0)
        
        elif target == "SpinBox_patten_width":
            self.patten_width = value
        
        elif target == "SpinBox_patten_T":
            self.patten_T = value
            self.Update_chartwidget(self.ui.widget_patten_set, mode=self.patten_choose)
        
        elif target == "SpinBox_patten_num":
            self.patten_num = value
            self.generate_patten_series()
        
        elif target == "SpinBox_patten_index":
            self.patten_index = value

        elif target == "SpinBox_patten_x_coordinate":
            self.patten_x_coordinate = value
            self.update_patten_series()

        elif target == "SpinBox_patten_y_coordinate":
            self.patten_y_coordinate = value
            self.update_patten_series()

        elif target == "doubleSpinBox_camera_expos":
            self.camera_expos = value

        elif target == "SpinBox_camera_frame":
            self.camera_frame = value

        elif target == 'spinbox_camera_gain':
            self.camera_gain = value

        elif target == 'spinbox_camera_ROIx':
            self.camera_ROIx = value

        elif target == 'spinbox_camera_ROIy':
            self.camera_ROIy = value

        elif target == 'spinbox_camera_ROIw':
            self.camera_ROIw = value

        elif target == 'spinbox_camera_ROIh':
            self.camera_ROIh = value
        
        elif target == "DoubleSpinBox_light_strength":
            self.light_strength = value

        elif target == 'SpinBox_scan_layer_num':
            self.scan_layer_num = value
            self.ui.PushButton_scaning.setEnabled(False)
        
        elif target == 'DoubleSpinBox_pzt_location':
            self.pzt_location = value
            self.ui.PushButton_scaning.setEnabled(False)
            try:
                self.moving_pzt()
            except:
                pass
        
        elif target == 'DoubleSpinBox_scan_step':
            self.scan_step = value
            self.scaning_step = value/1000
            self.ui.DoubleSpinBox_scaning_step.setValue(self.scaning_step)
            self.ui.DoubleSpinBox_pzt_location.setSingleStep(value/1000)
            self.ui.PushButton_scaning.setEnabled(False)
        
        elif target == 'threshold_value':
            self.threshold_value = value
            self.maskimg_thresholding()

        elif target == 'Spinbox_maskimg_index':
            self.maskimg_index = value
            self.maskimg_thresholding()

        elif target == 'Spinbox_image_group':
            self.image_group = value
            img = self.origin_data[self.image_group-1][self.image_browse_index-1]
            self.show_matplotlib_origin_image(img)

        elif target == 'image_index_slider':
            self.image_browse_index = value
            img = self.origin_data[self.image_group-1][self.image_browse_index-1]
            self.show_matplotlib_origin_image(img)
        
        elif target == 'x_coordinate':
            self.image_x_coordinate = value
        
        elif target == 'y_coordinate':
            self.image_y_coordinate = value
        
        elif target == 'DoubleSpinBox_scaning_step':
            self.scaning_step = value

        elif target == 'DoubleSpinBox_scale_index':
            self.scale_index = value
        
        elif target == 'section_line_coordinate':
            self.section_line_coordinate = value


    def mask_para_set(self):
        '''
        显示掩膜调节参数的一个tipview
        '''  
        position = TeachingTipTailPosition.BOTTOM
        self.mask_para_set_view = TeachingTipView(
            icon=None,
            title='掩膜设置',
            content='设置掩膜的一些参数',
            image=None,
            isClosable=True,
            tailPosition=position,
        )

        self.mask_para_set_view.button = PillPushButton('二值化')
        self.mask_para_set_view.button.setFixedWidth(120)
        self.mask_para_set_view.button.clicked.connect(self.maskimg_thresholding)

        self.mask_para_set_view.label_img_index = QLabel()
        self.mask_para_set_view.label_img_index.setText('图片序号')

        self.mask_para_set_view.Spinbox_maskimg_index = SpinBox()
        self.mask_para_set_view.Spinbox_maskimg_index.setMaximum(self.mask_num)
        self.mask_para_set_view.Spinbox_maskimg_index.setMinimum(1)
        self.mask_para_set_view.Spinbox_maskimg_index.setValue(self.maskimg_index)
        self.mask_para_set_view.Spinbox_maskimg_index.valueChanged.connect(functools.partial(self.upgrate_value, 'Spinbox_maskimg_index'))


        self.mask_para_set_view.ComboBox_threshold_method = ComboBox()
        items = ['普通阈值分割', '自适应阈值分割']
        self.mask_para_set_view.ComboBox_threshold_method.addItems(items)
        self.mask_para_set_view.ComboBox_threshold_method.setCurrentIndex(-1)
        self.mask_para_set_view.ComboBox_threshold_method.currentTextChanged.connect(functools.partial(self.ComboBox_textchange, 'ComboBox_threshold_method'))
        self.mask_para_set_view.ComboBox_threshold_method.setText(self.threshold_method)

        self.mask_para_set_view.label_threshold = QLabel()
        self.mask_para_set_view.label_threshold.setText("阈值")

        self.mask_para_set_view.threshold_value = SpinBox()
        self.mask_para_set_view.threshold_value.setMaximum(255)
        self.mask_para_set_view.threshold_value.setMinimum(0)
        self.mask_para_set_view.threshold_value.setValue(self.threshold_value)
        self.mask_para_set_view.threshold_value.valueChanged.connect(functools.partial(self.upgrate_value, 'threshold_value'))

        self.mask_para_set_view.button_generate_mask = PushButton('生成掩膜')
        self.mask_para_set_view.button_generate_mask.setFixedWidth(120)
        self.mask_para_set_view.button_generate_mask.clicked.connect(self.generate_mask_data)

        # 嵌套布局
        h1 = QHBoxLayout()
        h1.addWidget(self.mask_para_set_view.label_img_index)
        h1.addStretch(1)
        h1.addWidget(self.mask_para_set_view.Spinbox_maskimg_index)
        h1.addStretch(1)
        h1.addWidget(self.mask_para_set_view.ComboBox_threshold_method)
        h1.addStretch(1)
        h1.addWidget(self.mask_para_set_view.label_threshold)        
        h1.addStretch(1)
        h1.addWidget(self.mask_para_set_view.threshold_value)        
        h1.addStretch(1)
        h1.addWidget(self.mask_para_set_view.button)
        h1.addStretch(1)
        h1.addWidget(self.mask_para_set_view.button_generate_mask)

        hwg1=QWidget()
        hwg1.setLayout(h1)

        self.mask_para_set_view.addWidget(hwg1, align=Qt.AlignCenter)


        w = TeachingTip.make(
            target=self.ui.PushButton_mask_parm_set,
            view=self.mask_para_set_view,
            duration=-1,
            tailPosition=position,
            parent=self
        )
        self.mask_para_set_view.closed.connect(w.close)

    
    def browse_images(self):
        '''
        显示浏览npy文件图片的一个tipview
        '''  
        position = TeachingTipTailPosition.BOTTOM
        self.browse_images_view = TeachingTipView(
            icon=None,
            title='浏览图片',
            content='可以查看npy文件中的图片',
            image=None,
            isClosable=True,
            tailPosition=position,
        )

        self.browse_images_view.label = QLabel()
        self.browse_images_view.label.setText("图片组序")

        self.browse_images_view.Spinbox_image_group = SpinBox()
        try:
            self.browse_images_view.Spinbox_image_group.setMaximum(self.origin_data.shape[0])
        except:
            self.browse_images_view.Spinbox_image_group.setMaximum(1)
        self.browse_images_view.Spinbox_image_group.setMinimum(1)
        self.browse_images_view.Spinbox_image_group.setValue(self.image_group)
        self.browse_images_view.Spinbox_image_group.valueChanged.connect(functools.partial(self.upgrate_value, 'Spinbox_image_group'))

        self.browse_images_view.image_index_slider = Slider(Qt.Horizontal, self)
        self.browse_images_view.image_index_slider.setFixedWidth(200)
        try:
            self.browse_images_view.image_index_slider.setMaximum(self.origin_data.shape[1])
        except:
            self.browse_images_view.image_index_slider.setMaximum(1)
        self.browse_images_view.image_index_slider.setMinimum(1)
        self.browse_images_view.image_index_slider.setValue(self.image_browse_index)
        self.browse_images_view.image_index_slider.valueChanged.connect(functools.partial(self.upgrate_value, 'image_index_slider'))
        
        # 嵌套布局
        h1 = QHBoxLayout()
        h1.addWidget(self.browse_images_view.label)
        h1.addStretch(1)
        h1.addWidget(self.browse_images_view.Spinbox_image_group)        
        h1.addStretch(1)
        h1.addWidget(self.browse_images_view.image_index_slider)        

        hwg1=QWidget()
        hwg1.setLayout(h1)

        self.browse_images_view.addWidget(hwg1, align=Qt.AlignCenter)

        w = TeachingTip.make(
            target=self.ui.PushButton_browse_images,
            view=self.browse_images_view,
            duration=-1,
            tailPosition=position,
            parent=self
        )
        self.browse_images_view.closed.connect(w.close)


    def show_section_line(self):
        """
        显示层析剖线的tipview
        """
        position = TeachingTipTailPosition.BOTTOM
        self.show_section_line_view = TeachingTipView(
            icon=None,
            title='层析剖线显示',
            content="根据提供的索引显示对应行或对应列的索引",
            image=None,
            isClosable=True,
            tailPosition=position,
        )

        self.show_section_line_view.comobox = ComboBox()
        items = ['x方向', 'y方向']
        self.show_section_line_view.comobox.addItems(items)
        self.show_section_line_view.comobox.setCurrentIndex(-1)
        self.show_section_line_view.comobox.currentTextChanged.connect(functools.partial(self.ComboBox_textchange, 'ComboBox_choose_section_direction'))

        self.show_section_line_view.spinbox = DoubleSpinBox()
        self.show_section_line_view.spinbox.setMaximum(200)
        self.show_section_line_view.spinbox.setMinimum(0)
        self.show_section_line_view.spinbox.valueChanged.connect(functools.partial(self.upgrate_value, 'section_line_coordinate'))

        self.show_section_line_view.confirm_pushbutton = PushButton('确认')
        self.show_section_line_view.confirm_pushbutton.clicked.connect(functools.partial(self.Update_chartwidget, self.ui.widget_axial_envelope, 0, 'section_envelope'))
       
        # 嵌套布局
        h1 = QHBoxLayout()
        h1.addWidget(self.show_section_line_view.comobox)
        h1.addStretch(1)
        h1.addWidget(self.show_section_line_view.spinbox)        
        h1.addStretch(1)
        h1.addWidget(self.show_section_line_view.confirm_pushbutton)        
  
        hwg1=QWidget()
        hwg1.setLayout(h1)

        self.show_section_line_view.addWidget(hwg1, align=Qt.AlignCenter)

        w = TeachingTip.make(
            target=self.ui.PushButton_show_section_line,
            view=self.show_section_line_view,
            duration=-1,
            tailPosition=position,
            parent=self
        )
        self.show_section_line_view.closed.connect(w.close)

    
    def camera_parm_set(self):
        '''
        显示相机硬件参数的一个tipview
        '''  
        position = TeachingTipTailPosition.BOTTOM
        self.camera_parm_set_view = TeachingTipView(
            icon=None,
            title='相机设置',
            content='设置相机的一些参数',
            image=None,
            isClosable=True,
            tailPosition=position,
        )

        self.camera_parm_set_view.label1 = QLabel()
        self.camera_parm_set_view.label1.setText("相机帧率")

        self.camera_parm_set_view.spinbox_camera_frame = SpinBox()
        self.camera_parm_set_view.spinbox_camera_frame.setMaximum(249)
        self.camera_parm_set_view.spinbox_camera_frame.setMinimum(1)
        self.camera_parm_set_view.spinbox_camera_frame.valueChanged.connect(functools.partial(self.upgrate_value, 'SpinBox_camera_frame'))
        self.camera_parm_set_view.spinbox_camera_frame.setValue(self.camera_frame)

        self.camera_parm_set_view.label2 = QLabel()
        self.camera_parm_set_view.label2.setText("相机增益")

        self.camera_parm_set_view.spinbox_camera_gain = SpinBox()
        self.camera_parm_set_view.spinbox_camera_gain.setMaximum(4)
        self.camera_parm_set_view.spinbox_camera_gain.setMinimum(0)
        self.camera_parm_set_view.spinbox_camera_gain.valueChanged.connect(functools.partial(self.upgrate_value, 'spinbox_camera_gain'))
        self.camera_parm_set_view.spinbox_camera_gain.setValue(self.camera_gain)

        self.camera_parm_set_view.label3 = QLabel()
        self.camera_parm_set_view.label3.setText("相机ROI原点x")

        self.camera_parm_set_view.spinbox_camera_ROIx = SpinBox()
        self.camera_parm_set_view.spinbox_camera_ROIx.setMaximum(1440)
        self.camera_parm_set_view.spinbox_camera_ROIx.setMinimum(0)
        self.camera_parm_set_view.spinbox_camera_ROIx.setSingleStep(8)
        self.camera_parm_set_view.spinbox_camera_ROIx.valueChanged.connect(functools.partial(self.upgrate_value, 'spinbox_camera_ROIx'))
        self.camera_parm_set_view.spinbox_camera_ROIx.setValue(self.camera_ROIx)

        self.camera_parm_set_view.label4 = QLabel()
        self.camera_parm_set_view.label4.setText("相机ROI原点y")

        self.camera_parm_set_view.spinbox_camera_ROIy = SpinBox()
        self.camera_parm_set_view.spinbox_camera_ROIy.setMaximum(1080)
        self.camera_parm_set_view.spinbox_camera_ROIy.setMinimum(0)
        self.camera_parm_set_view.spinbox_camera_ROIy.setSingleStep(8)
        self.camera_parm_set_view.spinbox_camera_ROIy.valueChanged.connect(functools.partial(self.upgrate_value, 'spinbox_camera_ROIy'))
        self.camera_parm_set_view.spinbox_camera_ROIy.setValue(self.camera_ROIy)

        self.camera_parm_set_view.label5 = QLabel()
        self.camera_parm_set_view.label5.setText("相机ROI宽度")

        self.camera_parm_set_view.spinbox_camera_ROIw = SpinBox()
        self.camera_parm_set_view.spinbox_camera_ROIw.setMaximum(1440)
        self.camera_parm_set_view.spinbox_camera_ROIw.setMinimum(0)
        self.camera_parm_set_view.spinbox_camera_ROIw.setSingleStep(8)
        self.camera_parm_set_view.spinbox_camera_ROIw.valueChanged.connect(functools.partial(self.upgrate_value, 'spinbox_camera_ROIw'))
        self.camera_parm_set_view.spinbox_camera_ROIw.setValue(self.camera_ROIw)

        self.camera_parm_set_view.label6 = QLabel()
        self.camera_parm_set_view.label6.setText("相机ROI高度")

        self.camera_parm_set_view.spinbox_camera_ROIh = SpinBox()
        self.camera_parm_set_view.spinbox_camera_ROIh.setMaximum(1080)
        self.camera_parm_set_view.spinbox_camera_ROIh.setMinimum(0)
        self.camera_parm_set_view.spinbox_camera_ROIh.setSingleStep(8)
        self.camera_parm_set_view.spinbox_camera_ROIh.valueChanged.connect(functools.partial(self.upgrate_value, 'spinbox_camera_ROIh'))
        self.camera_parm_set_view.spinbox_camera_ROIh.setValue(self.camera_ROIh)

        # 嵌套布局
        v1 = QVBoxLayout()
        v1.addWidget(self.camera_parm_set_view.label1)
        v1.addStretch(1)
        v1.addWidget(self.camera_parm_set_view.spinbox_camera_frame) 

        v2 = QVBoxLayout()
        v2.addWidget(self.camera_parm_set_view.label2)
        v2.addStretch(1)
        v2.addWidget(self.camera_parm_set_view.spinbox_camera_gain)   

        v3 = QVBoxLayout()
        v3.addWidget(self.camera_parm_set_view.label3)
        v3.addStretch(1)
        v3.addWidget(self.camera_parm_set_view.spinbox_camera_ROIx) 

        v4 = QVBoxLayout()
        v4.addWidget(self.camera_parm_set_view.label4)
        v4.addStretch(1)
        v4.addWidget(self.camera_parm_set_view.spinbox_camera_ROIy)  

        v5 = QVBoxLayout()
        v5.addWidget(self.camera_parm_set_view.label5)
        v5.addStretch(1)
        v5.addWidget(self.camera_parm_set_view.spinbox_camera_ROIw) 

        v6 = QVBoxLayout()
        v6.addWidget(self.camera_parm_set_view.label6)
        v6.addStretch(1)
        v6.addWidget(self.camera_parm_set_view.spinbox_camera_ROIh) 

        vwg1 = QWidget()
        vwg1.setLayout(v1)

        vwg2 = QWidget()
        vwg2.setLayout(v2)

        vwg3 = QWidget()
        vwg3.setLayout(v3)

        vwg4 = QWidget()
        vwg4.setLayout(v4)

        vwg5 = QWidget()
        vwg5.setLayout(v5)

        vwg6 = QWidget()
        vwg6.setLayout(v6)

        h1 = QHBoxLayout()
        h1.addWidget(vwg1)
        h1.addWidget(vwg2)
        h1.addWidget(vwg3)
        h1.addWidget(vwg4)
        h1.addWidget(vwg5)
        h1.addWidget(vwg6)

        hwg1 = QWidget()
        hwg1.setLayout(h1)
        self.camera_parm_set_view.addWidget(hwg1)

        w = TeachingTip.make(
            target=self.ui.PushButton_camera_more_parm,
            view=self.camera_parm_set_view,
            duration=-1,
            tailPosition=position,
            parent=self
        )
        self.camera_parm_set_view.closed.connect(w.close)


    def show_axial_envelope(self):
        """
        显示轴线包络设置的tipview
        """
        position = TeachingTipTailPosition.BOTTOM
        self.show_axial_envelope_view = TeachingTipView(
            icon=None,
            title='轴向包络显示',
            content="根据提供的二维坐标值显示对应点的轴向包络",
            image=None,
            isClosable=True,
            tailPosition=position,
        )

        self.show_axial_envelope_view.label_x_coordinate = QLabel()
        self.show_axial_envelope_view.label_x_coordinate.setText("x坐标值:")

        self.show_axial_envelope_view.x_coordinate = DoubleSpinBox()
        self.show_axial_envelope_view.x_coordinate.setMaximum(999)
        self.show_axial_envelope_view.x_coordinate.setMinimum(0)
        self.show_axial_envelope_view.x_coordinate.setValue(0)
        self.show_axial_envelope_view.x_coordinate.valueChanged.connect(functools.partial(self.upgrate_value, 'x_coordinate'))

        self.show_axial_envelope_view.label_y_coordinate = QLabel()
        self.show_axial_envelope_view.label_y_coordinate.setText("y坐标值:")

        self.show_axial_envelope_view.y_coordinate = DoubleSpinBox()
        self.show_axial_envelope_view.y_coordinate.setMaximum(999)
        self.show_axial_envelope_view.y_coordinate.setMinimum(0)
        self.show_axial_envelope_view.y_coordinate.setValue(0)
        self.show_axial_envelope_view.y_coordinate.valueChanged.connect(functools.partial(self.upgrate_value, 'y_coordinate'))

        self.show_axial_envelope_view.confirm_pushbutton = PushButton('确认')
        self.show_axial_envelope_view.confirm_pushbutton.clicked.connect(functools.partial(self.Update_chartwidget, self.ui.widget_axial_envelope, self.ui.stackedWidget_show_view.currentIndex(), 'axial_envelope'))
       
        # 嵌套布局
        h1 = QHBoxLayout()
        h1.addWidget(self.show_axial_envelope_view.label_x_coordinate)
        h1.addStretch(1)
        h1.addWidget(self.show_axial_envelope_view.x_coordinate)        
        h1.addStretch(1)
        h1.addWidget(self.show_axial_envelope_view.label_y_coordinate)        
        h1.addStretch(1)
        h1.addWidget(self.show_axial_envelope_view.y_coordinate)        
        h1.addStretch(1)
        h1.addWidget(self.show_axial_envelope_view.confirm_pushbutton)       


        hwg1=QWidget()
        hwg1.setLayout(h1)

        self.show_axial_envelope_view.addWidget(hwg1, align=Qt.AlignCenter)

        w = TeachingTip.make(
            target=self.ui.PushButton_show_axial_envelope,
            view=self.show_axial_envelope_view,
            duration=-1,
            tailPosition=position,
            parent=self
        )
        self.show_axial_envelope_view.closed.connect(w.close)


    def create_save_csv_SuccessInfoBar(self, filename):
        # convenient class mothod
        InfoBar.success(
            title='成功提示',
            content= filename+"保存成功",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            # position='Custom',   # NOTE: use custom info bar manager
            duration=5000,
            parent=self
        )


    def process_state_tip(self):
        if self.mainprocess_stateTooltip:
            self.mainprocess_stateTooltip.setContent('轮廓生成啦 😆')
            self.mainprocess_stateTooltip.setState(True)
            self.mainprocess_stateTooltip = None
        else:
            self.mainprocess_stateTooltip = StateToolTip('正在生成轮廓', '客官请耐心等待哦~~', self)
            self.mainprocess_stateTooltip.move(1200, 30)
            self.mainprocess_stateTooltip.show()
            QApplication.processEvents()


######################################################
# 硬件功能区


    @QtCore.Slot()
    def setexternalpattern(self):
        # dmd外部模式流参数设置
        if self.DMD_Status == True:
        # 调用 DisplayExternalPatternStreaming 函数
            preilluminationtime = int(self.DMD_pre_expo*1000)
            illuminationtime = int(self.DMD_expo*1000)
            postilluminationtime = int(self.DMD_post_expo*1000)
            self.dll_ControlDMD.DisplayExternalPatternStreaming(c_ubyte(self.DMD_per_frame),c_uint(preilluminationtime),
                                                     c_uint(illuminationtime),c_uint(postilluminationtime))
        else:
            print("Please check out the DMD power/interface connection!!!")
    
   
    @QtCore.Slot()
    def changeDMDfps(self):
        # 设置新的分辨率和帧率
        new_width = 1920
        new_height = 1080
        new_refresh_rate = self.DMD_frequency

        self.current_settings.PelsWidth = new_width
        self.current_settings.PelsHeight = new_height
        self.current_settings.DisplayFrequency = new_refresh_rate

        # 应用新的显示设置
        # result = win32api.ChangeDisplaySettings(current_settings, win32con.CDS_UPDATEREGISTRY | win32con.CDS_SET_PRIMARY)
        result = win32api.ChangeDisplaySettingsEx(self.device_name,self.current_settings, win32con.CDS_UPDATEREGISTRY | 0)
        if result == win32con.DISP_CHANGE_SUCCESSFUL:
            print("Resolution and Refresh Rate set successfully.")
        else:
            print(f"Failed to set resolution and refresh rate. Error Code: {result}")


    def calculate_DMD_parameter(self):
        """
        自动计算DMD的帧前、帧持续、帧后参数
        """
        try:
            per_frame_time = (1000/self.DMD_frequency - self.pzt_move_time)/self.DMD_per_frame
            self.DMD_pre_expo = 0.12*per_frame_time
            self.DMD_expo = 0.78*per_frame_time
            self.DMD_post_expo = 0.1*per_frame_time
            self.ui.DoubleSpinBox_pre_expo.setValue(self.DMD_pre_expo)
            self.ui.DoubleSpinBox_expo.setValue(self.DMD_expo)
            self.ui.DoubleSpinBox_post_expo.setValue(self.DMD_post_expo)
        except:
            pass
        
    
    def DMD_curve_show(self):
        """
        显示DMD脉冲曲线
        """
        perframe = [[0,0.01],[self.DMD_pre_expo,0.01],[self.DMD_pre_expo,0.9],[self.DMD_pre_expo+self.DMD_expo,0.9], [self.DMD_pre_expo+self.DMD_expo,0.01],[self.DMD_pre_expo+self.DMD_expo+self.DMD_post_expo,0.01]]
        frame_curve = []
        for i in range(self.DMD_per_frame):
            for j in range(len(perframe)):
                _n = perframe[j][0] + i*(self.DMD_pre_expo+self.DMD_expo+self.DMD_post_expo)
                frame_curve.append([_n, perframe[j][1]])
                # print(frame_curve)
        frame_curve.append([1000/self.DMD_frequency+0.01, 0.01])
        return frame_curve 
    
    
    def generate_patten_series(self):

        sum = self.patten_num
        T = self.patten_T
        self.patten_series = []     # 这个是真正用于生成条纹的
        self.patten_series_show = []        # 这个是显示在chart上需要的
        n = 1
        for i in range(T):
            for j in range(T):
                if n <= sum:
                    self.patten_series.append([j, i])
                    if self.patten_choose == "横线线列":
                        self.patten_series_show.append([i+0.5, j+0.5, n])
                    else:
                        self.patten_series_show.append([j+0.5, i+0.5, n])
                n += 1
            
        self.ui.widget_patten_set.option['series'][0]['data']=self.patten_series_show
        self.ui.widget_patten_set.option['visualMap'][0]['max']=self.patten_num-1
        self.ui.widget_patten_set.setChartOptions(self.ui.widget_patten_set.option)
    

    def update_patten_series(self):
        # 将重叠位置的序列在显示上分开，但是传递给生成图案函数的序列依然不变
        n = 0
        x_show = self.patten_x_coordinate
        y_show = self.patten_y_coordinate
        for row in self.patten_series:
            if row == [self.patten_x_coordinate-1, self.patten_y_coordinate-1]:
                n += 0.1
                x_show = self.patten_x_coordinate + n
                y_show = self.patten_y_coordinate + n

        self.patten_series[self.patten_index-1] = [self.patten_x_coordinate-1, self.patten_y_coordinate-1]
        if self.patten_choose == "横线线列":
            self.patten_series_show[self.patten_index-1] = [y_show-1+0.5, x_show-1+0.5, self.patten_index]
        else:
            self.patten_series_show[self.patten_index-1] = [x_show-1+0.5, y_show-1+0.5, self.patten_index]
        self.ui.widget_patten_set.option['series'][0]['data']=self.patten_series_show
        self.ui.widget_patten_set.setChartOptions(self.ui.widget_patten_set.option)

    
    def generate_patten(self):
        print("条纹周期:",self.patten_T)
        print("条纹宽度:",self.patten_width)
        print('条纹模式:',self.patten_choose)
        print("条纹序列:",self.patten_series)
        print("条纹序列显示:",self.patten_series_show)
        
        try:
            pygame.quit()
        except:
            pass
        pygame.init()

        # 显示器坐标检测
        Monitor = EnumDisplayMonitors()
        Widgh_DMD = int(Monitor[1][2][2] - Monitor[1][2][0])
        Hight_DMD = int(Monitor[1][2][3] - Monitor[1][2][1])
        Widgh_in = int(Monitor[1][2][0])
        Hight_in = int(Monitor[1][2][1])

        os.environ['SDL_VIDEO_WINDOW_POS'] = f'{Widgh_in},{Hight_in}'

        screen = pygame.display.set_mode((1920,1080), OPENGL|DOUBLEBUF|NOFRAME)
        
        W, H = screen.get_size()
        width = 1.0
        height = (float(H)/W)*width
        print(W,H,width,height)
        glMatrixMode(GL_PROJECTION)
        gluOrtho2D(-W/2, +W/2, -H/2, +H/2)  # 设置正交投影矩阵
        glMatrixMode(GL_MODELVIEW)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)    # 清空
        if self.patten_choose == "点阵阵列":
            self.generate_point_array(self.patten_width, self.patten_width*self.patten_T, self.patten_series)
        elif self.patten_choose == "横线线列":
            self.generate_line_array(self.patten_width, self.patten_width*self.patten_T, self.patten_series)
        elif self.patten_choose == "竖线线列":
            self.generate_line_array(self.patten_width, self.patten_width*self.patten_T, self.patten_series)
        pygame.display.flip()
        print("success")
    

    def generate_line_array(self, w, T, series):

        uint = np.gcd(w, T)     # 获得栅格宽度与栅格周期的最大公因数作为最小单位
        w_uint = w/uint
        T_uint = T/uint

        H = 1080
        W = 1920

        colors = [(0,0,1), (0,0,2), (0,0,4), (0,0,8), (0,0,16), (0,0,32), (0,0,64), (0,0,128),
                (0,1,0), (0,2,0), (0,4,0), (0,8,0), (0,16,0), (0,32,0), (0,64,0), (0,128,0),
                (1,0,0), (2,0,0), (4,0,0), (8,0,0), (16,0,0), (32,0,0), (64,0,0), (128,0,0)]
        # colors = [(0,0,255), (0,255,0), (255,0,0),(0,255,255), (255,255,255)]
        
        glBegin(GL_QUADS)       # 开始绘图
        color_index = 0
        for line in series:

            glColor3ub(*colors[color_index])  # 设置颜色
            if self.patten_choose == "横线线列":
                for i in range(-int(H/2/T), int(H/2/T)):      # 画出横条纹
                    glVertex2f(-W/2, T*i-line[0]*w)
                    glVertex2f(W/2, T*i-line[0]*w)
                    glVertex2f(W/2, (T*i+w)-line[0]*w)
                    glVertex2f(-W/2, (T*i+w)-line[0]*w)
            elif self.patten_choose == "竖线线列":
                for i in range(-int(W/2/T), int(W/2/T)): 
                    glVertex2f(T*i-line[0]*w, H/2)
                    glVertex2f((T*i+w)-line[0]*w, H/2)
                    glVertex2f((T*i+w)-line[0]*w, -H/2)
                    glVertex2f(T*i-line[0]*w, -H/2)
            color_index += 1
        glEnd()

    
    def generate_point_array(self, w, T, series):
        """
        生成点阵, 该程序会自动生成不同位置下的光斑, 来填满整个屏幕, 因此在设置DMD时序的时候, 需要在一帧里设置(T/w)^2个脉冲才能全部显示
        Args:
            w为光斑的宽度, 单位为像素
            T为光斑的周期, 单位为像素, 周期必须要是w的整数倍
        """
        # 设置点大小
        glPointSize(w)

        colors = [(0,0,1), (0,0,2), (0,0,4), (0,0,8), (0,0,16), (0,0,32), (0,0,64), (0,0,128),
                (0,1,0), (0,2,0), (0,4,0), (0,8,0), (0,16,0), (0,32,0), (0,64,0), (0,128,0),
                (1,0,0), (2,0,0), (4,0,0), (8,0,0), (16,0,0), (32,0,0), (64,0,0), (128,0,0)]
        # colors = [(0,0,255), (0,255,0), (255,0,0),(0,255,255), (255,255,255)]
        # 只绘制端点
        glBegin(GL_POINTS)
        color_index = 0
        W=1920
        H=1080

        # 做点阵集
        for point in series:
            glColor3ub(*colors[color_index])
            for i in range(-int(W/2/T),int(W/2/T)):
                for j in range(-int(H/2/T), int(H/2/T)):
                    glVertex2f(T*i+point[0]*w, T*j-point[1]*w)
            color_index += 1
            # print(color_index)
        print(color_index)

        glEnd()


    @QtCore.Slot()
    def camera_init(self):
        # 初始化相机
        try:
            self.Camera.uninit_camera()
        except:
            pass
        self.Camera = My_Camera('宽场相机') 
        
        self.camera_parameters_dict = {'type':'Galaxy',
                                       'exposure':self.camera_expos,
                                       'gain':6*self.camera_gain,
                                       'fps':self.camera_frame,
                                       'gamma':1,
                                       'offsetx':self.camera_ROIx, #ROI起始点,左上角
                                       'offsety':self.camera_ROIy,
                                       'width':self.camera_ROIw,
                                       'height':self.camera_ROIh,
                                       'contrast':0,
                                       'undistort':False,
                                       'save':None,  
                                       'win_w':None,
                                       'win_h':None,
                                       'index':1} # 设置相机参数
        self.Camera.init_camera(self.camera_parameters_dict) # 初始化相机
        self.camera_timer = QTimer()
        self.camera_timer.timeout.connect(self._display_camera_stream) 
        self.camera_timer.start(int(1000/self.Camera.fps))


    @QtCore.Slot()
    def camera_work(self):
        print(self.ui.PushButton_camera_work.isChecked())
        if self.ui.PushButton_camera_work.isChecked() == True:
            self.ui.PushButton_camera_work.setText("继续")
            self.ui.PushButton_camera_save.setEnabled(True)
            self.camera_timer.stop()
        else:
            self.ui.PushButton_camera_work.setText("暂停")
            self.ui.PushButton_camera_save.setEnabled(False)
            # 初始化相机
            self.camera_timer = QTimer()
            self.camera_timer.timeout.connect(self._display_camera_stream) 
            self.camera_timer.start(int(1000/self.Camera.fps))
    

    @QtCore.Slot()
    def camera_img_save(self):
        self.Select_existing_folder("PushButton_camera_save")

        name = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        imgfile = name + '-imgs.bmp'
        cv2.imwrite(os.path.join(self.imgfolder_path, imgfile), self.img_temp)


    @QtCore.Slot()
    def moving_pzt(self):
        # 将pzt移动至指定位置，单位为微米
        # print(self.pzt_location)
        self.Daq.control_pzt(self.pzt_location)
        
    
    @QtCore.Slot()    
    def scan_init(self):
        """
        三维扫描的初始化设置
        """

        # 启动相机触发
        self.cameratrigger()
        #设置图像的四维矩阵
        self.origin_data = np.zeros([self.DMD_per_frame,self.scan_layer_num,self.camera_ROIh,self.camera_ROIw])    
        self.savefig = Thread(target=self.triggergetfigure)  

        voltage_now = 0.0454*self.pzt_location
        scan_step_voltage = self.scan_step/1000*0.0454

        data_array = (c_double * 2)(voltage_now, voltage_now)
        # 创建 MyStruct 结构体实例
        self.mystruct = MyStruct()

        # 为结构体成员变量赋值
        self.mystruct.numbegin = 0
        self.mystruct.numend = self.scan_layer_num
        self.mystruct.voltageperlayer = scan_step_voltage
        self.mystruct.fun1 = CFUNCTYPE(None)(self.mulithread)  # 将函数指针赋值给函数
        self.mystruct.fun2 = CFUNCTYPE(None)(self.over_closeandsave)  # 将函数指针赋值给函数
        self.mystruct.data[0] = data_array[0]
        self.mystruct.data[1] = data_array[1]     

        # 调用 DAQcontrol 函数
        stime_pulse = self.DMD_per_frame*(self.DMD_pre_expo+self.DMD_expo+self.DMD_post_expo)*10 
        self.dll_DAQ.DAQcontrol(stime_pulse, pointer(self.mystruct))

        self.ui.PushButton_scaning.setEnabled(True)
        self.ui.PushButton_save_npy.setEnabled(True)
        print("initial over #V#")


    # 开始三维层析的函数
    @QtCore.Slot()    
    def begintomeasure(self):

        self.dll_DAQ.StartDAQtask()
        self.t1 = time.time()

    
    # 用进程的方式开启相机采集
    def mulithread(self):
        if self.scaning_flag == False:
            
            self.scaning_flag = True
            # 开始保存图片
            self.savefig.start()

    
    # 接受相机采集的图片
    def triggergetfigure(self):
        time.sleep(0.002)
        self.camera.stream_on() # 数据流开启

        for i in range(self.origin_data.shape[1]): 
            for j in range(self.origin_data.shape[0]):
                a1 = time.time()
                # get raw image
                raw_image = self.camera.data_stream[0].get_image()
                a2 = time.time()
                if raw_image == None:
                    print("donot data")
                else:
                # create numpy array with data from raw image
                    numpy_image = raw_image.get_numpy_array()
                    self.origin_data[j,i,:,:] = numpy_image
        self.origin_data = np.flip(self.origin_data, axis=1)



    # 测量结束，关闭设备，初始化相机
    def over_closeandsave(self):

        self.savefig.join()
        print(f"The time of running:{time.time()-self.t1} s")
        self.camera.stream_off()    # 数据流结束 
        self.camera.close_device()  # 关闭相机
        self.scaning_flag = False   # 扫描线程标志位关闭
    

    def save_data_npy(self):

        self.Select_existing_folder('PushButton_save_npy')
        name = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        datafile = name + '-imgs.npy'
        
        np.save(op.join(self.datanpyfolder_path, datafile), self.origin_data)
        print('successfully')

    
    # 把相机设置为触发模式
    def cameratrigger(self):
        # 设置连续获取模式
        try:
            self.camera_timer.stop()
        except:
            pass
        try:
            self.Camera.uninit_camera()
        except:
            pass
        try:
            self.camera.stream_off() # 数据流结束
        except:
            pass
        try:
            self.camera.close_device()
        except:
            pass

        
        gx_device_manager = gx.DeviceManager()
          
        self.camera = gx_device_manager.open_device_by_index(1)
        self.camera.TriggerMode.set(gx.GxSwitchEntry.ON) # 外触发
        self.camera.TriggerSource.set(gx.GxTriggerSourceEntry.LINE2) # 外触发信号来自Line2
        self.camera.ExposureTime.set(self.camera_expos*1000) # us
        self.camera.Gain.set(6*self.camera_gain)
        # 设置相机的区域   这里面四个数必须是8的倍数
        self.camera.OffsetX.set(self.camera_ROIx) 
        self.camera.OffsetY.set(self.camera_ROIy) 
        self.camera.Width.set(self.camera_ROIw) 
        self.camera.Height.set(self.camera_ROIh)
        self.camera.data_stream[0].set_acquisition_buffer_number(1) 


######################################################
# 软件功能区
        

    def maskimg_thresholding(self):
        
        if self.mask_type == 'img':
            img = cv2.imread(self.Maskimgpath, 0) 
        elif self.mask_type == 'npy':
            img = self.maskimgs_set[self.maskimg_index-1]

        # 设定阈值
        threshold_value = self.threshold_value
        mode = self.threshold_method
        img = np.array(img, dtype=np.uint8)

        if mode == "自适应阈值分割":
          # 自适应阈值滤波
            self.Mask_thresholding = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)
        
        elif mode == "普通阈值分割":
            ret, self.Mask_thresholding = cv2.threshold(img, threshold_value, 255, cv2.THRESH_BINARY)

        kernel = np.ones((3,3), np.uint8)   # 形态学开运算
        self.Mask_thresholding = cv2.erode(self.Mask_thresholding, kernel, iterations=1)
        # filtered_image = cv2.dialate(filtered_image, kernel, iterations=1)

        if not self.mask_para_set_view.button.isChecked():
            self.show_matplotlib_mask_image(img)
        else:
            self.show_matplotlib_mask_image(self.Mask_thresholding)


    def generate_mask_data(self):

        self.Select_existing_folder('button_generate_mask')

        if self.mask_type == 'img':
            maskimg = cv2.imread(self.Maskimgpath, 0) 
            maskarea = self.Mask_thresholding
            self.generate_single_mask_data(maskimg, maskarea, 0)
        
        elif self.mask_type == 'npy':

            # 对所有的掩膜图片进行阈值分割
            threshold_value = self.threshold_value
            mode = self.threshold_method
            img_binary_sets = np.empty_like(self.maskimgs_set)

            for i in range(self.maskimgs_set.shape[0]):
                if mode == "自适应阈值分割":
                # 自适应阈值滤波
                    img_binary = cv2.adaptiveThreshold(self.maskimgs_set[i], 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)
                
                elif mode == "普通阈值分割":
                    ret, img_binary = cv2.threshold(self.maskimgs_set[i], threshold_value, 255, cv2.THRESH_BINARY)

                kernel = np.ones((3,3), np.uint8)   # 形态学开运算
                img_binary = cv2.erode(img_binary, kernel, iterations=1)
                img_binary_sets[i] = img_binary
            
            thread_sum = img_binary_sets.shape[0]
            self.multithread_mask_list = [None] * thread_sum     # 生成单个线程中将会返回的数据存储列表

            for i in range(thread_sum):
                self.generate_single_mask_data(self.maskimgs_set[i], img_binary_sets[i], i)
                self.ui.ProgressBar_generate_mask_2.setValue(100*(i+1)/thread_sum)
            
            print('完成')

            name = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
            datafile = name + '-mask'
            self.save_list_2_csv(self.multithread_mask_list, op.join(self.mask_save_path, datafile))


    def generate_single_mask_data(self, maskimg, maskarea, i):

        if self.generate_mask_method == "预先法":
        
            # 找轮廓
            mask_img = maskimg
            maskarea = np.array(maskarea, dtype=np.uint8)
            contours, hierarchy = cv2.findContours(maskarea, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        # 获得轮廓内的数据的坐标
        data, data_all = self.find_contours_data(contours, 2448, 2048)

        # 获取每个有效轮廓的中心坐标，即不规则针孔阵列
        _img_arr = np.transpose([mask_img, mask_img], (1, 2, 0))
        center_point_coordinate = self.select_center(data, _img_arr)

        # 拟合得到规则的针孔阵列
        mask_data = self.fit_mask_data(center_point_coordinate, maskimg)

        if self.mask_type == 'img':
            self.save_list_2_csv(mask_data, "mask_1117_2x2")

            # 将生成的区域显示出来
            mask_img = np.repeat(mask_img[:, :, np.newaxis], 3, axis=2)

            masked_img = self.paint_point(mask_img, mask_data)
            self.show_matplotlib_mask_image(masked_img)

        elif self.mask_type == 'npy':
            self.multithread_mask_list[i] = mask_data

    
    def find_contours_data(self, contours, w, h):
        
        """
        该函数用于获取输入的轮廓集内的所有点的坐标,并将其按照单独的每个轮廓进行存储
        Arg:
            contours  通过轮廓识别函数得到的轮廓数据
            w  图片集的宽度
            h  图片集的高度
        Out:
            data 输出的是一个二维列表,列表的第一维代表第几个轮廓,第二维代表对应轮廓中包含的点的坐标,存储的单元为[x,y]
            data_all 输出的是一个一维列表,没有按照单一轮廓进行存储,而是全部存储在了同一维度中
        """
        
        print("输入的轮廓数：", len(contours))
        
        data = []   # 二维列表 每个轮廓的点单独放
        data_all = []   # 所有轮廓的点集中在一起
        num = 0     # 与输出结果进行校验

        for i in range(len(contours)):
            
            self.ui.ProgressBar_generate_mask.setValue(100*i/len(contours))
            self.ui.label_generate_mask_process.setText(str(np.round(100*i/len(contours), 2))+"%")
            QApplication.processEvents()

            area = cv2.contourArea(contours[i], False)
            if area>0:
                
                num = num + 1

                # p = np.zeros((int(np.sqrt(10*area)),int(np.sqrt(10*area))))
                p = np.zeros((h ,w))
                cv2.drawContours(p, contours, i, 255, -1)

                # 计算轮廓质心
                moments = cv2.moments(contours[i])
                CY = int(moments["m10"]/moments["m00"])
                CX = int(moments["m01"]/moments["m00"])

                p = p[CX-int(0.5*np.sqrt(10*area)):CX+int(0.5*np.sqrt(10*area)), CY-int(0.5*np.sqrt(10*area)):CY+int(0.5*np.sqrt(10*area))]

                a = (np.where(p==255)[0]+(CX-int(0.5*np.sqrt(10*area)))).reshape(-1,1)
                b = (np.where(p==255)[1]+(CY-int(0.5*np.sqrt(10*area)))).reshape(-1,1)

                # p = np.zeros((h ,w))
                # cv2.drawContours(p, contours, i, 255, -1)
                # a = np.where(p==255)[0].reshape(-1, 1)
                # b = np.where(p==255)[1].reshape(-1, 1)
                coordinate = np.concatenate([a,b], axis=1).tolist()
                data.extend([coordinate])
                data_all.extend(coordinate)
        
        print("输出的轮廓数：", len(data), num)
        return data, data_all
    

    def select_center(self, data, img_arr):
        
        '''
        获得每个轮廓的光强中心点
        Arg:
            data  轮廓的数据集
            img_arr  三维图片集数据,h*w*n
        Out:
            point_coordinate  光强中心点的坐标集
        '''

        point_coordinate = []

        for area in data:
            area_value = []
            for i in range(len(area)):
                area_value.append(img_arr[area[i][0]][area[i][1]])
            area_value = np.array(area_value)
            # 找到最大值的对应索引
            try :
                coordinate = np.argmax(area_value)
                # 将一维索引转换为二维索引
                max_row_index, max_col_index = np.unravel_index(coordinate, area_value.shape)

                # area[max_row_index]及时光斑中心的坐标
                # show_section_line(img_arr, area[max_row_index][0], area[max_row_index][1], 0.5)
                point_coordinate.append(area[max_row_index])

            except ValueError:    # 可能是空列表
                pass
        
        return point_coordinate
    

    def fit_mask_data(self, points, maskimg):

        # 构建kd树
        kdtree_points = KDTree(points)
        
        # 得到规则点阵的点间距
        d = self.get_point_distance(points, kdtree_points)

        # 得到规则点阵的行数与列数
        row, col = self.get_points_col_row(maskimg, points, d)   # 80 100

        # 生成初始位置下的规则点阵
        origin_mask = self.generate_original_mask_grid(row, col, d)
        # origin_mask = self.generate_multi_original_mask_grid(row, col, d, 4)

        # 定位原始散点集靠中心的点用于点阵位移
        locate_point = self.locate_point(points, kdtree_points, maskimg, d)

        # 计算规则点阵中离这个点最近的点移到这个位置的偏移量，并实现偏移
        useful_mask = self.calculate_mask_offset(origin_mask, locate_point)

        return useful_mask


    def calculate_mask_offset(self, origin_mask, locate_point):

        # 创建关于规则点阵的kdtree用于计算离定位点最近的点
        kdtree1 = KDTree(origin_mask)

        # 最近的邻居点的索引和距离
        dd1, indexes = kdtree1.query([locate_point], k=4)
        indexes = indexes.flatten()

        d = origin_mask[indexes[0]]-locate_point
        d = np.tile(d, (origin_mask.shape[0], 1))

        useful_mask = origin_mask-d

        return useful_mask


    def locate_point(self, points, kdtree, maskimg, d):

        # 找到距离中心位置最近的k个点
        mask_img = maskimg
        dd, indexes = kdtree.query([[mask_img.shape[0]/2,mask_img.shape[1]/2]], k=4)
        indexes = indexes.flatten()

        # 从最靠近中心的那个点开始判定，看看那个点是不是符合要求
        for i in range(4):
            dd1, indexes1 = kdtree.query([points[indexes[i]]], k=5)
            mean1 = np.mean(dd1[0][1:5])

            if np.abs(d-mean1)<0.5:
                break
        
        return points[indexes[i]]


    def generate_multi_original_mask_grid(self, row, col, d, n):
        data0 = np.linspace(0, col*d, n*col, endpoint=False)
        data0 = np.round(data0).astype(int)
        data1 = np.linspace(0, row*d, n*row, endpoint=False)
        data1 = np.round(data1).astype(int)

        cols = np.tile(data0, (n*row+1, 1))
        cols = np.reshape(cols, (1, -1))
        cols = cols.flatten()

        rows = np.tile(data1, (n*col+1, 1))
        rows = np.transpose(rows, (1,0))
        rows = np.reshape(rows, (1, -1))
        rows = rows.flatten()

        # 使用 numpy.stack() 函数合并数组
        original_mask_grid = np.stack((rows, cols), axis=1)
        return original_mask_grid


    def generate_original_mask_grid(self, row, col, d):
        data0 = np.linspace(0, (col-1)*d, col, endpoint=True)
        data0 = np.round(data0).astype(int)
        data1 = np.linspace(0, (row-1)*d, row, endpoint=True)
        data1 = np.round(data1).astype(int)

        cols = np.tile(data0, (row, 1))
        cols = np.reshape(cols, (1, -1))
        cols = cols.flatten()

        rows = np.tile(data1, (col, 1))
        rows = np.transpose(rows, (1,0))
        rows = np.reshape(rows, (1, -1))
        rows = rows.flatten()

        # 使用 numpy.stack() 函数合并数组
        original_mask_grid = np.stack((rows, cols), axis=1)
        return original_mask_grid
    

    def get_points_col_row(self, mask_img, points, d):
        
        row = np.zeros(mask_img.shape[0])
        col = np.zeros(mask_img.shape[1])
        
        points = np.array(points)
        for i in range(mask_img.shape[0]):
            # 指定区间
            lower_bound = i
            upper_bound = i+0.8*d
            # 使用向量化操作计算在行区间内点的数量
            count = np.sum((points[:, 0] >= lower_bound) & (points[:, 0] <= upper_bound) )
            row[i] = count
        col_count = np.round((np.percentile(row,50)+np.percentile(row,80))/2)
        col_count = int(col_count-1)  # 规则针孔有几列

        for i in range(mask_img.shape[1]):
            # 指定区间
            lower_bound = i
            upper_bound = i+0.8*d
            # 使用向量化操作计算在行区间内点的数量
            count = np.sum((points[:, 1] >= lower_bound) & (points[:, 1] <= upper_bound) )
            col[i] = count
        row_count = np.round((np.percentile(col,50)+np.percentile(col,80))/2)
        row_count = int(row_count-1)  # 规则针孔有几行

        return row_count, col_count

    
    def get_point_distance(self, points, kd_tree):

        # 最近的四个邻居点的索引和距离
        dd, _ = kd_tree.query(points, k=5)
        closest_points = dd[:,1:5]

        data = np.reshape(closest_points,(1,-1))
        data = data.flatten()

        # 对数组进行排序
        sorted_arr = np.sort(data)

        # 计算要排除的值的数量,这里认为前20%与后20%均是异常值需排除
        exclude_count = int(0.1 * len(sorted_arr))

        # 使用切片操作排除最大和最小的20%值
        trimmed_arr = sorted_arr[exclude_count: -exclude_count]

        # 计算剩余值的平均值
        mean_value = np.mean(trimmed_arr)

        # print("去除异常值后的平均值：", mean_value)
        return mean_value


    def generate_tomography(self):
        start_time = time.time()
        self.process_state_tip()

        
        self.thread1_endevent = False
        self.thread1.start()
        print("并行线程开始")

        while(self.thread1_endevent == False):
            QApplication.processEvents()
            
        print('三维形貌的形状', self.tomography_2d.shape)
        self.show_matplotlib_image(self.tomography_2d)
        print("成功结束")
        print(time.time()-start_time)
        self.process_state_tip()
    

    def generate_multithread(self):
        """
        这是一个多线程的生成形貌函数
        首先会得到需要的线程数, 并且创建出其子线程并启动, 之后该线程便会堵塞, 直到所有子线程执行完毕
        子线程计算出n*3的点云数据后会存在self.multithread_value_list列表里, 本线程会将其合并成self.point_cloud, 之后正常处理
        """
        thread_sum = self.origin_data.shape[0]
        threads = []
        self.multithread_value_list = [None] * thread_sum     # 生成单个线程中将会返回的数据存储列表
        self.multithread_pointcloud_list = [None] * thread_sum
        self.multithread_value_nan_list = [None] * thread_sum
        for i in range(thread_sum):
            t = Thread(target=self.generate_tomography_multithread_thread, args=(self.origin_data[i], self.multithread_mask_list[i], i))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()

        # 得到点云数据
        self.point_cloud = np.vstack(self.multithread_pointcloud_list)
        # 确定数组的形状
        shapes = [arr.shape for arr in self.multithread_value_list]
        common_shape = np.min(shapes, axis=0)

        # 创建一个公共部分数组
        self.tomography_2d = np.zeros(common_shape)

        # 将公共部分相加
        for arr in self.multithread_value_list:
            sliced_arr = arr[:common_shape[0], :common_shape[1]]
            self.tomography_2d += sliced_arr

        # 去毛刺
        if self.remove_bur_status is True:
            laplacian = np.abs(cv2.Laplacian(self.tomography_2d, -1, ksize=3)) # 求梯度
            mask = np.where(laplacian>50, 1, 0).astype(np.uint8) # 选取梯度过大的地方，做成遮罩
            self.tomography_2d = cv2.inpaint(self.tomography_2d.astype(np.float32), mask, 3, cv2.INPAINT_NS) # 修补
            print('quchu')    
        
        if self.incline_calibration_status is True:
            self.tomography_2d = self.fitting_plane(self.tomography_2d)       # 倾斜校正
        
        self.tomography_2d = cv2.medianBlur(self.tomography_2d.astype(np.float32), 3)
        self.thread1_endevent = True
        self.thread1 = Thread(target=self.generate_multithread)    # 线程重置

        print("并行线程结束")
    

    def Interpolation_filling(self, data_2d):
    
        """
        该函数用于利用拟合的方法填补含nan的二维数组
        Arg: 
            data_2d 含nan的二维数组
        Out:
            data_2d_full 不含nan的二维数组
        """
        
        if self.interpolation_method == '不插值':
            data_2d_full = data_2d
        else:
            print("开始拟合")
            start_time = time.time()

            # 获取有效值的索引位置
            valid_indices = np.where(~np.isnan(data_2d))

            # 提取有效值的行和列
            rows = valid_indices[0]
            cols = valid_indices[1]

            # 提取有效值
            valid_values = data_2d[rows, cols]

            # 创建interp2d对象并执行插值
            interp_func = interp2d(rows, cols, valid_values, kind = "linear")

            # 生成插值结果
            data_2d_full = interp_func(np.arange(data_2d.shape[0]), np.arange(data_2d.shape[1]))
            data_2d_full = data_2d_full.T

            # 拟合过程有有可能出现极大异常值与极小异常值，因此需要对极大异常值进行校正
            # 定义阈值
            threshold_h = np.nanmax(data_2d)+1
            threshold_l = np.nanmin(data_2d)-1
            # print(threshold_h, threshold_l)

            # 将原数组最大最小值设为阈值
            # data_2d_full[data_2d_full > threshold_h] = threshold_h
            # data_2d_full[data_2d_full < threshold_l] = threshold_l

            # 寻找异常大值的索引
            outliers_max = np.where(data_2d_full > threshold_h)

            # 循环遍历每个异常大值的索引
            for i, j in zip(outliers_max[0], outliers_max[1]):
                # 计算除了该点外邻域的均值
                neighborhood = np.delete(data_2d_full[max(0, i-1):i+2, max(0, j-1):j+2], (1, 1))
                neighborhood_mean = np.nanmin(neighborhood)

                # 更新异常大值的值为邻域均值
                data_2d_full[i, j] = neighborhood_mean

            # 寻找异常大值的索引
            outliers_min = np.where(data_2d_full < threshold_l)

            # 循环遍历每个异常小值的索引
            for i, j in zip(outliers_min[0], outliers_min[1]):
                # 计算除了该点外邻域的均值
                neighborhood = np.delete(data_2d_full[max(0, i-1):i+2, max(0, j-1):j+2], (1, 1))
                neighborhood_mean = np.nanmax(neighborhood)

                # 更新异常大值的值为邻域均值
                data_2d_full[i, j] = neighborhood_mean

            print("拟合时间：", time.time()-start_time)

            x = np.linspace(0, data_2d_full.shape[1]-1, data_2d_full.shape[1])
            y = np.linspace(data_2d_full.shape[0]-1, 0, data_2d_full.shape[0])
            X, Y = np.meshgrid(x, y)
            envelope_points_cloud = np.hstack((X.reshape(-1,1), Y.reshape(-1,1), data_2d_full.reshape(-1,1)))
            self.point_cloud_scaled = envelope_points_cloud

        return data_2d_full
    

    def fitting_plane(self, arr_2d):
        """
        对输入的二维数组进行抽样,对抽样得到的点进行线性拟合得到平面
        """
        # 对该数组进行线性拟合
        # 生成网格坐标
        sampled_arr = arr_2d
        x = np.linspace(sampled_arr.shape[1]-1, 0, sampled_arr.shape[1])
        y = np.linspace(0, sampled_arr.shape[0]-1, sampled_arr.shape[0])
        x, y = np.meshgrid(x, y)
        xflatten = x.flatten()
        yflatten = y.flatten()
        # 展平数据和坐标
        X = np.column_stack((xflatten, yflatten))
        y = sampled_arr.flatten()

        # 添加偏置列
        X = np.c_[X, np.ones(X.shape[0])]

        # 去除非nan值
        non_nan_indices_y = np.argwhere(~np.isnan(y)).flatten()
        y = y[non_nan_indices_y]
        X = X[non_nan_indices_y]

        # 计算最小二乘解
        coefficients, residuals, _, _ = np.linalg.lstsq(X, y, rcond=None)

        # 提取平面系数
        a, b, c = coefficients

        # 计算校正量
        correction = (a * xflatten + b * yflatten + c).reshape(sampled_arr.shape)
        _c = 150/(np.max(correction)-np.min(correction))*correction+np.min(correction)
        _c = np.array(_c,dtype=np.uint8)
        cv2.imwrite("incline.jpg", _c)

        # 去倾斜校正
        corrected_data = arr_2d - correction

        return corrected_data

    
    def return_2_2d(self, array):
    
        """
        该函数用于将三维的点云转为2维数组
        Arg: 
            point_cloud n行3列的点云数据
        Out:
            result_array 返回w*h的二维数组,缺失值用nan填补
        """

        # 获取行索引、列索引和值
        rows = array[:, 0].astype(int)
        rows = rows[::-1]
        cols = array[:, 1].astype(int)
        cols = cols[::-1]
        values = array[:, 2]
        values = values[::-1]

        # 确定二维数组的大小
        n_rows = int(np.max(rows)) + 1
        n_cols = int(np.max(cols)) + 1

        # 创建二维数组并填充值
        result_array = np.full((n_rows, n_cols), np.nan)
        result_array[rows, cols] = values

        return result_array

    
    def generate_tomography_multithread_thread(self, images, maskdata, i):
        """
        单个子线程执行的部分, 包括读取图片, 读取掩膜, 计算中心坐标, 生成点云与放缩
        """
        # 重新整合图片的形状为h*w*n
        images = np.transpose(images, (1, 2, 0))    

        # 获取每个有效轮廓的中心坐标
        center_point_coordinate = maskdata

        # 生成点云数据
        point_cloud = self.calculate_tomography(center_point_coordinate, images, self.tomography_method)

        # 转为二维数组
        point_cloud_2d_nan = self.return_2_2d(point_cloud)      # 缺失值为nan

        # 去除所有的nan对二维数组进行整型
        point_cloud_2d = self.reshape_2d_array(point_cloud_2d_nan, i)

        # 结束，返回数据
        self.multithread_value_list[i] = point_cloud_2d
        self.multithread_value_nan_list[i] = point_cloud_2d_nan
        self.multithread_pointcloud_list[i] = point_cloud

    
    def reshape_2d_array(self, point_cloud_2d, i):

        # 去除所有的全nan行
        point_cloud_2d = np.array([row for row in point_cloud_2d if not np.isnan(row).all()])

        # 去除所有的全nan列
        point_cloud_2d = np.array([row for row in point_cloud_2d.T if not np.isnan(row).all()]).T

        # 计算是几倍周期
        T = int(np.ceil(np.sqrt(self.origin_data.shape[0])))

        # 创建一个全零的大数组，形状为原数组的6倍
        new_arr = np.zeros((point_cloud_2d.shape[0]*T, point_cloud_2d.shape[1]*T))

        # 将原数组的值复制到新数组的对应位置
        j = int((T-1) - i%T)
        k = int(i // T)
        # print(j,k,T)
        # print(point_cloud_2d.shape)
        new_arr[j::T, k::T] = point_cloud_2d

        return new_arr

    
    def scale_xy(self, _point_cloud, k = 1):
        
        """
        由于筛选后的点在xy上过于稀疏,因此需要通过放缩来进行重采样
        Arg:
            point_cloud  点云数据
            k 缩放系数
        """

        point_cloud = _point_cloud.copy()   # 如果不加这行，将会同时改变self.point_cloud
        # 提取第一列
        first_column = point_cloud[:, 0]
        modified_column = first_column * k
        point_cloud[:, 0] = modified_column

        # 提取第二列
        second_column = point_cloud[:, 1]
        modified_column = second_column * k
        point_cloud[:, 1] = modified_column

        return point_cloud
    

    def calculate_tomography(self, point_coordinate, data_3d, mode):
        
        """
        计算三维形貌,即轴向包络最大值
        Arg:
            point_coordinate  所需计算的每个二维像素点的位置
            data_3d  三维层析数据,格式为w*h*n
            mode  光强中心提取模式
        Out:
            point_cloud  点云数组,shape为n*3
        """
        
        d = self.scaning_step   # 采样点实际间距，单位微米
        z = d*np.arange(1,data_3d.shape[2]+1)
        # print(z)
        # print(point_coordinate)
        point_coordinate = np.array(point_coordinate)
        point_cloud = np.hstack((point_coordinate, np.zeros((point_coordinate.shape[0], 1))))    # 将n*2的数组变为n*3的数组，新增为0
        
        if mode == "质心法":

          print("开始质心法")

          # 采用半高宽法提高精度
          for i in range(len(point_coordinate)):
              
            dataz = data_3d[point_coordinate[i][0], point_coordinate[i][1]]
            # 生成第一组掩膜，掩膜为最大值周围1/3的数据
            mask = np.zeros(len(dataz))
            # print(np.nanmax(dataz), np.nanargmax(dataz))
            max_value = np.nanargmax(dataz)
            max_index = int(max_value+1/6*len(dataz)) if int(max_value+1/6*len(dataz))<len(dataz) else len(dataz)
            min_index = int(max_value-1/6*len(dataz)) if int(max_value-1/6*len(dataz))>0 else 0
            # print(max_index, min_index)
            mask[min_index:max_index] = 1
            dataz = np.multiply(dataz, mask)
            # print(mask)
            # 生成第二组掩膜，掩膜为全峰半宽
            mask = np.where(dataz > 0.5*(np.max(dataz)+np.min(dataz)), 1, 0)
            dataz_fwhm = np.multiply(dataz, mask)
            #  print(dataz_fwhm)
            center = np.sum(dataz_fwhm*z, axis=0) / np.sum(dataz_fwhm, axis=0)

            point_cloud[i][2] = center

        elif mode == "极值法":
            
            print("开始极值法")
            for i in range(len(point_coordinate)):
                center = np.argmax(data_3d[point_coordinate[i][0], point_coordinate[i][1]])

                point_cloud[i][2] = center
        
        elif mode == "高斯法":

            print("开始高斯法")
            # 保留中心坐标所在的数据，并重整为二维数组
            data = data_3d[point_coordinate[:, 0], point_coordinate[:, 0]]
            data = np.clip(data, 0.01, 255)

            # # 选取最大值附近1/3的数据
            max_value = np.max(data, axis=1)
            # mask = (1e-6)*np.ones_like(data)
            # data_len = data.shape[1]
            
            # for i in range(data.shape[0]):
            #     max_index = int(max_value[i]+1/6*data_len) if int(max_value[i]+1/6*data_len)<data_len else data_len
            #     min_index = int(max_value[i]-1/6*data_len) if int(max_value[i]-1/6*data_len)>0 else 0
            #     mask[i][min_index:max_index] = 1
            # data = np.multiply(data,mask)

            # 选取半高宽数据
            data_max = max_value
            data_max = data_max.reshape(-1,1)
            data_min = np.min(data, axis=1)
            data_min = data_min.reshape(-1,1)
            w = np.where(data>(data_max+data_min*0.5)/2, 1, 1e-6)      
            w = w.reshape(w.shape[0], w.shape[1], 1)
            eye = np.eye(data.shape[1])    
            w = w * eye  
            y_extend = data.reshape(w.shape[0], w.shape[1], 1)

            x_extend = np.arange(0, data.shape[1]).reshape(1, data.shape[1], 1)
            x_extend = np.repeat(x_extend, data.shape[0], axis=0)

            x_2 = x_extend**2
            x_1 = x_extend
            x_0 = np.ones((data.shape[0], data.shape[1], 1))

            A = np.concatenate((x_2, x_1, x_0), axis=2)
            b = np.log(y_extend)

            _t = np.transpose(A, axes=[0,2,1])
            print(_t.shape, w.shape)
            _q1 = np.einsum("ijk,ikn->ijn", _t, w)
            _q = np.einsum("ijk,ikn->ijn", _q1, A)
            _w = np.linalg.pinv(_q)
            _e = np.einsum("ijk,ikn->ijn", _w, _t)
            r = np.einsum("ijk,ikn->ijn", _e, w)
            res = np.einsum("ijk,ikn->ijn", r, b)
            # print(res)

            Z = -(res[:, 1]*0.5/res[:, 0])
            print(np.max(Z))
            Z = np.nan_to_num(Z, nan=0)
            print(np.max(Z), np.min(Z))
            Z = np.clip(Z, 0, data.shape[1])

            point_cloud = np.hstack((point_coordinate,Z))
            print(point_cloud.shape)


        print("轮廓计算结束")
        return point_cloud


######################################################
# 通用功能区
        

    def _display_camera_stream(self):
        img = self.Camera.snap()
        self.img_temp = img
        img = resize_for_show_win(img, self.ui.label_camera_show.geometry().height(), self.ui.label_camera_show.geometry().width())
        if img.ndim==2:
            img = cv2.merge([img, img, img])
        img = QImage(img, img.shape[1], img.shape[0], img.strides[0], QImage.Format_BGR888)
        self.ui.label_camera_show.setPixmap(QPixmap.fromImage(img))


    def Select_existing_folder(self, target):
        """
        跳出选择文件夹的界面,选中文件夹后输出文件夹的路径,并传递给输出框显示
        Arg:
            target  ui控件的名称,便于显示时输出至对应输出框
        """
        if target == "PushButton_camera_save":
            
            imgfolder_path = QFileDialog.getExistingDirectory(self, "选择文件夹") 
            if imgfolder_path == '':
                print("none")
            else:
                self.imgfolder_path = imgfolder_path 
        
        elif target == 'PushButton_save_npy':

            datanpyfolder_path = QFileDialog.getExistingDirectory(self, "选择文件夹") 
            if datanpyfolder_path == '':
                print("none")
            else:
                self.datanpyfolder_path = datanpyfolder_path 
        
        elif target == "SearchLineEdit_npypath":
            
            origin_npypath = QFileDialog.getOpenFileName(self, "选择npy文件") 
            if origin_npypath == '':
                print("none")
            else:
                self.origin_npypath = origin_npypath[0]
                self.ui.SearchLineEdit_npypath.setText(self.origin_npypath)
                print(self.origin_npypath)
                self.origin_data = np.load(self.origin_npypath)  # 读取该文件
        
        elif target == "SearchLineEdit_maskpath":
            
            _maskpath = QFileDialog.getOpenFileName(self, "选择掩膜csv文件")
            if _maskpath == '':
                print("none")
            else:
                self.Maskpath = _maskpath[0]
                self.ui.SearchLineEdit_maskpath.setText(self.Maskpath)
                self.multithread_mask_list = self.read_csv_2_list(self.Maskpath)
        
        elif target == "SearchLineEdit_imgmask_path":
            
            _maskimgpath = QFileDialog.getOpenFileName(self, "选择掩膜图片")
            if _maskimgpath == '':
                print("none")
            else:
                self.Maskimgpath = _maskimgpath[0]
                self.ui.SearchLineEdit_imgmask_path.setText(self.Maskimgpath)

                # 判断文件类型
                parts = self.Maskimgpath.split('.')
                if len(parts) > 1:
                    if parts[-1] == 'npy':
                        self.mask_type = 'npy'
                        _maskimgs_set = np.load(self.Maskimgpath)
                        self.maskimgs_set = _maskimgs_set[:, 0, :, :]
                        self.mask_num = self.maskimgs_set.shape[0]
                        self.show_matplotlib_mask_image(self.maskimgs_set[0])
                    else:
                        self.mask_type = 'img'
                        self.mask_num = 1
                        _img = cv2.imread(self.Maskimgpath)
                        self.show_matplotlib_mask_image(_img)
                else:
                    print('文件类型错误')
        
        if target == "button_generate_mask":
            
            mask_save_path = QFileDialog.getExistingDirectory(self, "选择文件夹") 
            if mask_save_path == '':
                print("none")
            else:
                self.mask_save_path = mask_save_path 
                

    def show_matplotlib_origin_image(self, img):
        
        # 创建一个 Matplotlib Figure 对象
        figure = Figure()

        # 在 Figure 上绘制图形
        axes = figure.add_subplot(111)
        norm = mcolors.TwoSlopeNorm(vmin=0, vcenter=127, vmax=255)

        image = axes.imshow(img, cmap="gray", norm=norm)  
        axes.set_label('Intensity')

        # 创建一个 FigureCanvas 对象，并将 Figure 传递给它
        canvas = FigureCanvas(figure)
        toolbar = NavigationToolbar2QT(canvas, self)

        # 创建一个垂直布局，并将 FigureCanvas 添加到其中
        layout = QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(canvas)
   
        # 创建一个 QWidget，并将布局设置为它的布局，用于显示掩膜区域
        self.matplotlib_widget_mask = QWidget()
        self.matplotlib_widget_mask.setLayout(layout)
        self.ui.stackedWidget_show_view.removeWidget(self.ui.stackedWidget_show_view.widget(0))
        self.ui.stackedWidget_show_view.insertWidget(0, self.matplotlib_widget_mask)
        self.ui.SegmentedWidget.setCurrentItem(0)
        self.ui.stackedWidget_show_view.setCurrentIndex(0)


    def show_matplotlib_mask_image(self, img):
        
        # 创建一个 Matplotlib Figure 对象
        figure = Figure()

        # 在 Figure 上绘制图形
        axes = figure.add_subplot(111)

        image = axes.imshow(img, cmap="gray")  
        axes.set_label('Intensity')

        # 创建一个 FigureCanvas 对象，并将 Figure 传递给它
        canvas = FigureCanvas(figure)
        toolbar = NavigationToolbar2QT(canvas, self)

        # 创建一个垂直布局，并将 FigureCanvas 添加到其中
        layout = QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(canvas)
   
        # 创建一个 QWidget，并将布局设置为它的布局，用于显示掩膜区域
        self.matplotlib_widget_mask = QWidget()
        self.matplotlib_widget_mask.setLayout(layout)
        self.ui.stackedWidget_show_view.removeWidget(self.ui.stackedWidget_show_view.widget(1))
        self.ui.stackedWidget_show_view.insertWidget(1, self.matplotlib_widget_mask)
        self.ui.SegmentedWidget.setCurrentItem(1)
        self.ui.stackedWidget_show_view.setCurrentIndex(1)


    def show_matplotlib_image(self, img):
        
        # 创建一个 Matplotlib Figure 对象
        figure = Figure()

        # 在 Figure 上绘制图形
        axes = figure.add_subplot(111)
        max_value = np.nanpercentile(img, 99)
        min_value = np.nanpercentile(img, 1)
        print(max_value, min_value)

        norm = mcolors.TwoSlopeNorm(vmin=min_value, vcenter=0.5*(max_value+min_value), vmax=max_value)

        # 设置横纵坐标的实际范围
        xmax = self.origin_data.shape[3]*self.camera_uint_size/self.camera_scaled_index
        ymax = self.origin_data.shape[2]*self.camera_uint_size/self.camera_scaled_index

        image = axes.imshow(img, extent=[0, xmax, ymax, 0], cmap="cool", norm = norm, origin="upper") 
        axes.set_xlabel("横坐标(微米)", fontproperties="SimHei")
        axes.set_ylabel("纵坐标(微米)", fontproperties="SimHei")        
        colorbar = figure.colorbar(image, pad = 0.05, fraction=0.05)
        axes.set_label('Intensity')

        # 创建一个 FigureCanvas 对象，并将 Figure 传递给它
        canvas = FigureCanvas(figure)
        toolbar = NavigationToolbar2QT(canvas, self)

        # 创建一个垂直布局，并将 FigureCanvas 添加到其中
        layout = QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(canvas)

        # 创建一个 QWidget，并将布局设置为它的布局，用于显示三维形貌的二维强度
        self.matplotlib_widget = QWidget()
        self.matplotlib_widget.setLayout(layout)
        self.ui.stackedWidget_show_view.removeWidget(self.ui.stackedWidget_show_view.widget(2))
        self.ui.stackedWidget_show_view.insertWidget(2, self.matplotlib_widget)
        self.ui.SegmentedWidget.setCurrentItem(2)
        self.ui.stackedWidget_show_view.setCurrentIndex(2)


    def save_ply(self):

        point_cloud = np.array(self.point_cloud)

        pcd = o3d.geometry.PointCloud()

        pcd.points = o3d.utility.Vector3dVector(point_cloud)
        o3d.io.write_point_cloud("cloud.ply", pcd)
        self.create_save_csv_SuccessInfoBar("cloud.ply")

        x = np.linspace(0, self.tomography_2d.shape[1]-1, self.tomography_2d.shape[1])
        y = np.linspace(self.tomography_2d.shape[0]-1, 0, self.tomography_2d.shape[0]) # 图像坐标的原点在左上角 三维坐标的原点定义在左下角
        X, Y = np.meshgrid(x, y)

        data = np.hstack((X.reshape(-1,1), Y.reshape(-1,1), self.tomography_2d.reshape(-1,1))) # 此时形貌点云的xyz值


        row = self.tomography_2d.shape[0]
        col = self.tomography_2d.shape[1]

        # 生成颜色
        c = data[:,2].copy().reshape(-1)
        c = (c-c.min())/(c.max()-c.min())
        # c = mpl.cm.viridis(c)

        c = matplotlib.cm.jet(c)
        c = np.round(255*c)
            
        # 生成带颜色的点云数据
        points_cloud = np.hstack((data, c[:,:3]))
            
        # 计算面片四角的索引
        points_total_num = col*row
        face_num = (col-1)*(row-1)
        points_num_per_face = np.repeat(np.array([[4]]), face_num, axis=0)

        points_index = np.arange(points_total_num).reshape(row, col)
        first_point_index = (points_index[:-1,:-1]).reshape(-1,1)
        second_point_index = (points_index[:-1,1:]).reshape(-1,1)
        third_point_index = (points_index[1:,:-1]).reshape(-1,1)
        fourth_point_index = (points_index[1:,1:]).reshape(-1,1)

        face_element = np.hstack((points_num_per_face,
                                first_point_index,
                                second_point_index,
                                fourth_point_index,
                                third_point_index
                                ))

        header_1 = 'ply\nformat ascii 1.0\ncomment made by Xzl\ncomment this file is a envelope\n'
        header_2 = 'element vertex %d\nproperty float x\nproperty float y\nproperty float z\n'%(data.shape[0])
        header_3 = 'property uchar red\nproperty uchar green\nproperty uchar blue\n'
        header_4 = 'element face %d\nproperty list uchar int vertex_index\nend_header'%(face_num)
        header = header_1+header_2+header_3+header_4


        np.savetxt('mesh.ply', points_cloud, fmt='%.6f %.6f %.6f %d %d %d', header=header, comments='')
        with open('mesh.ply', 'a') as f:
            np.savetxt(f, face_element, fmt='%d %d %d %d %d', comments='')
        print('done')

    
    def show_mesh(self):
        reader_mesh = vtk.vtkPLYReader()
        reader_mesh.SetFileName('mesh.ply')
        reader_mesh.Update()

        # 定义/设置映射器
        mapper_mesh = vtk.vtkPolyDataMapper()
        mapper_mesh.SetInputConnection(reader_mesh.GetOutputPort())
        # mapper_mesh.GetInput().GetPointData().SetScalars(array)

        # 定义/设置actor
        actor_mesh = vtk.vtkActor()
        actor_mesh.SetMapper(mapper_mesh)

        render = vtk.vtkRenderer()
        render.AddActor(actor_mesh)

        renWin = vtk.vtkRenderWindow()
        renWin.AddRenderer(render)

        local_pos = self.ui.stackedWidget_show_view.pos()
        global_pos = self.ui.stackedWidget_show_view.mapToGlobal(local_pos)
        renWin.SetPosition(global_pos.x(), global_pos.y()-50)  
        renWin.SetSize(800, 600)  
        renWin.SetWindowName("面片图展示")  # 设置渲染窗口的名称

        iren = vtk.vtkRenderWindowInteractor()
        iren.SetRenderWindow(renWin)

        renWin.Render()
        iren.Initialize()
        iren.Start()


    def read_csv_2_list(self, filename):
        # 从CSV文件中读取二维列表
        with open(filename, 'r') as file:
            reader = csv.reader(file)
            data = list(reader)
        
        # print(data)
        # 将字符串还原为列表
        restored_data = [[list(map(int, re.findall(r'\d+', value))) for value in row] for row in data]

        print('CSV文件读取成功:', filename)   
        return restored_data
    

    def save_list_2_csv(self, data, filename):
        
        data = list(data)
        # 将二维列表保存为CSV文件
        filename = filename + '.csv'
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(data)

        print('CSV文件保存成功:', filename)
        self.create_save_csv_SuccessInfoBar(filename)
        self.Maskpath = filename
        self.ui.SearchLineEdit_maskpath.setText(self.Maskpath)


    def incline_calibration(self):
        self.incline_calibration_status = self.ui.SwitchButton_incline_calibration.isChecked()

    def remove_bur(self):
        self.remove_bur_status = self.ui.SwitchButton_remove_bur.isChecked()


    def paint_point(self, img, data):
    
        '''批量画点'''

        # 定义要修改的颜色
        new_color = [0, 255, 0]  # 设置为绿色
        

        for point in data:
            x ,y = point[0], point[1]
            img[x, y] = new_color
        
        return img


# 主程序    
if __name__ == "__main__": # 主程序入口
    # 设置程序的一些配置
    setLicense("asnnjEIGl6NTRcAa/1zcaPyJYnzbIrkvjbm9iVMoHpG6nzmKwzLt5H1nNMyf+0sx5IynMhZuu1GvNCD1ea/Jq2qCCV8EjLoTYaabxcbG/HzDWtlt8jlvZha5x1DpLFhrdvca75APYuqT94YpVM7aecNrn0SPSkveviOvgmJ5TVM5oqddJ0d8tYsFE2mdWDebmhO6Rp9A8yhqJhrNkDC4YJkBYLv+8QZnaGqkTbjGIktVV1KO5Pl4H7/21qKPmugv")
    app = QtWidgets.QApplication([])

    # 实例化主界面
    widget = MainWindow() # 实例化主界面
    widget.show() # 显示

    # 设置关闭程序的步骤
    ret = app.exec()
    sys.exit(ret)