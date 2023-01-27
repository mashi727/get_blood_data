import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6 import QtGui
from PySide6.QtGui import QPen, QColor

import pandas as pd
import numpy as np
import pyqtgraph as pg
from PySide6 import QtWidgets, QtCore
from PySide6 import QtCore 
from datetime import datetime 

from dataVizUi import Ui_MainWindow

class TimeAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super(TimeAxisItem, self).__init__(*args, **kwargs)

    def tickStrings(self, values, scale, spacing):
        # %Yは、yyyyを表すみたい
        return [datetime.fromtimestamp(v).strftime('%Y %m/%d') for v in values]

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.show()
        self.init_ui()
        self.win = self.graphicsView
        
        df = pd.read_csv('./blood_data_sorted.csv', index_col=0,usecols=[0,*range(2, 20)])
        self.df = df.set_index(pd.to_datetime(df.index, format='%Y-%m-%d'))
        self.dt = self.df.index.astype(np.int64)//10**9
        #print(self.dt)
        
        cols=df.columns
        
        #cols = ['血圧（最高）','血圧（最低）','脈拍','ALT（GPT）','γ-GTP','総蛋白TP','アルブミンALB','ALB/G','CHOL','GALB','RBC','Hb','Ht','MCV','MCH','MCHC','WBC','PLT']
        
        graph_obj = []
        for i in range(len(cols)):
            graph_obj.append('p'+str(f"{i}"))

        num_of_fold = 5
        
        num = len(graph_obj)+1
        for case in range(1,num):
            graph_id = graph_obj[case-1]
            graph_label = cols[case-1]
            # 凡例のフォントの大きさと、表示するテキストの指定
            #legend = '<font size=\'5\' color=\'#FFFFFF\'>'+ 'λ='+str(average_num) +'</font>'
            self.graph_id = self.set_graph_ui(graph_id, case, num_of_fold, graph_label)
            self.plot_xy(graph_id, graph_label)
            self.vb = self.graph_id.vb
    
    def init_ui(self):
        # Windowサイズを設定
        self.setGeometry(100, 100, 2300, 1400)

    def set_graph_ui(self,graph_id, num, num_of_fold, graph_label):
        # いつもは、こちら。
        setprop = lambda x: (x.showGrid(x=True, y=True, alpha = 1),x.setAutoVisible(y=True), x.addLegend(), x.showGrid(x=True, y=True))
        # setAutoVisible(y=True)を有効にすると、IndexError: boolean index did not match indexed array along dimension 0;
        # dimension is 39 but corresponding boolean dimension is 40 がでます。
        #setprop = lambda x: (x.showGrid(x=True, y=True, alpha = 1), x.addLegend(offset=(0,5.5)), x.showGrid(x=True, y=True))
        styles = {'color':'white','font-size':'20px', 'font-style':'bold'}
          
        graph_id = self.win.addPlot()
        #graph_id.setTitle('<font size=\'5\' color=\'#FFFFFF\'>'+ 'Histogram' +'</font>')
        graph_id.setLabel('left', text=graph_label, units='', **styles)
        #graph_id.setLabel('bottom', text='献血日', units='', **styles)
        setprop(graph_id)
        self.graph_id = graph_id
        if num % num_of_fold == 0:
            self.win.nextRow()
        return graph_id



    def plot_xy(self,graph_id, graph_label):
        pass
        s = self.df[graph_label]
        s_rolling = self.df[graph_label].rolling(3).mean()
        legend = '<font size=\'5\' color=\'#FFFFFF\'>'+ str(graph_id) +'</font>'
        # Create a plot with a date-time axis
        #self.graph_id(pg.PlotWidget(axisItems={'bottom': TimeAxisItem(orientation='bottom')}))
        #self.graph_id.plot(self.dt, s, name=legend,alpha=1 ,symbolPen=pg.mkPen(color=(255, 255, 0)),symbolBrush=(255, 255, 0,100), symbolSize=10, pen=None, symbol='o')
        self.graph_id.addItem(pg.PlotDataItem(self.dt, s, pen='w',axisItems={'bottom': TimeAxisItem(orientation='bottom')}))
        self.graph_id.addItem(pg.PlotDataItem(self.dt, s_rolling, pen=pg.mkPen((255,255,255,128), width=5)))
        
        pass


app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
