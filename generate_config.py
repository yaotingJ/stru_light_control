import os
import os.path as op
import yaml


class My_Config():
	def __init__(self):
		self.config_path = 'config/config.yaml'
  
		self.config = {}

  
	def read(self, path=''):
		if path=='':
			if op.exists(self.config_path): # 存在配置文件
				with open(self.config_path, 'r', encoding='utf-8') as f:
					self.config = yaml.load(f.read(), Loader=yaml.FullLoader)
			else: # 若没有配置文件，生成它
				print('不存在配置文件', self.config_path)
				self.write('software')
		else:
			with open(path, 'r', encoding='utf-8') as f:
				self.config = yaml.load(f.read(), Loader=yaml.FullLoader)



	def write(self, mode='software'):
		'''
		写配置文件
  		'''
		# 检查是否存在 config 文件夹
		if op.exists('config'):
			pass
		else:
			os.mkdir('config') # 不存在则创建

		# 写配置文件
		if mode=='software':
			# 写
			print('写入中')
			with open(self.software_config_path, 'w', encoding='utf-8') as f:
				yaml.dump(self.original_software_config(), f)
			print('完毕')
		elif mode=='chip':
			# 写
			print('写入中')
			with open(self.software_config_path, 'w', encoding='utf-8') as f:
				yaml.dump(self.original_chip_config(), f)
			print('完毕')
  
  
	def original_software_config(self):
		'''
		原始的软件配置文件
  		'''
		config = {
      		'是否自动自检': True, 
        	'版本': '1.0-dev', 
         	'相机': {
              	'相机类型': 'Galaxy', 
            	'相机序号': 1, 
            	'视场': {
                	'单位': '微米', 
                	'物镜1': 1000}},
          	'共焦': {
               	'行数': 256, 
                '列数': 256, 
                'X偏置': 0, 
                'Y偏置': 0, 
                'PMT1增益': 0.4, 
                'PMT2增益': 0.26, 
                '扫描范围': 1, 
                '扫描策略': '光栅', 
                'PZT位置': 250, 
                'PZT最大位置': 450, 
                'PZT最小位置': 50, 
                '层数': 50, 
                '激光强度': 2.16, 
                'pzt灵敏度': 46.263, 
                '超调量1': 1.125, 
                '超调量2': 0.25, 
                '波头长度': 200, 
                '波尾长度': 200, 
                '显示最大值': 5, 
                '视场': {
                    '单位': 1, 
                    '基准视场电压': 0.5, 
                    '物镜1': 3600}}, 
        	'数采卡': {
            	'振镜': 'Dev2/ao0:1', 
             	'PMT_控制': 'Dev2/ao2', 
              	'PZT': 'Dev2/ao3', 
               	'PMT_信号': 'Dev2/ai0', 
                '同步_发出': '/Dev2/PFI14', 
                '同步_接收': '/Dev2/PFI12'}, 
         	'位移台': {
              	'z向缩放': 0.1, 
               	'档位1': {
                	'步进': 0.01, 
                 	'速度': 0.01, 
                  	'加速度': 0.01}, 
                '档位2': {
                    '步进': 0.05, 
                    '速度': 0.05, 
                    '加速度': 0.05}, 
                '档位3': {
                    '步进': 0.1, 
                    '速度': 0.1, 
                    '加速度': 0.1}, 
                '档位4': {
                    '步进': 0.5, 
                    '速度': 0.5, 
                    '加速度': 0.5}, 
                '档位5': {
                    '步进': 1.0, 
                    '速度': 1.0, 
                    '加速度': 1.0}, 
                '档位6': {
                    '步进': 10.0, 
                    '速度': 5.0, 
                    '加速度': 5.0}}, 
			'激光器': {
       			'电流值': 50},
        	'测试': {
            	'单机测试': True, 
             	'共焦测试数据': 'data/2022-12-10-10-26-11---0.5-256-50-96.0-111.0.npz', 
              	'变焦测试数据': 'data/test-1/*.bmp', 
               	'地图测试数据': 'data/x%.1fy%.1f.png'}}

		return config


	def original_chip_config(self):
		'''
		原始的芯片配置文件
  		'''
		config = {
			'型号0': {
       			'名字': '测试芯片', 
          		'模型': 'data/model/chip_mode1.STL', 
            	'标志位图像': 'data/template/temp.bmp', 
             	'标志位坐标': [0, 0, 0], 
              	'芯片中心坐标': [0, 0, 0], 
               	'芯片四角坐标': {
                    '左上角': [-10, 21, 0], 
                    '左下角': [-10, -8, 0], 
                    '右下角': [44, -9, 0], 
                    '右上角': [44, 21, 0]}, 
                '测量位置坐标': {
                    '左上角': [5, 0, 0], 
                    '左下角': [-5, 0, 0], 
                    '右下角': [0, 2, 0], 
                    '右上角': [0, -1, 0]}, 
                '测量软限位': {'Z下限': -20}
                }
   			}

		return config
