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

# 基準値の設定
standard_data = {}
standard_data['血圧（最高）'] = 130
standard_data['血圧（最低）'] = 85
standard_data['ALT（GPT）'] = (8,49,'IU/L')
standard_data['γ-GTP'] = (9,68,'IU/L')
standard_data['総蛋白TP'] = (6.6,8.2, 'g/dL')
standard_data['アルブミンALB'] = (4.0,5.1,'g/dL')
standard_data['ALB/G'] = (1.3,2.1,'')
standard_data['CHOL'] = (140,259,'mg/dL')
standard_data['GALB'] = (16.5,'%')
standard_data['RBC'] = (418,560,'x10^4 /μL')
standard_data['Hb'] = (12.7,17.0,'g/dL')
standard_data['Ht'] = (38.8,50.0,'%')
standard_data['MCV'] = (83.0,99.5,'fL')
standard_data['MCH'] = (26.8,33.5,'pg')
standard_data['MCHC'] = (31.7,35.2,'%')
standard_data['WBC'] = (38,89,'x10^2 /μL')
standard_data['PLT'] = (17.0,36.5,'x10^4/μL')




class TimeAxisItem(pg.AxisItem):
    '''
    時間をを表示する。
    UNIX時間を以下の様にJSTに変換する。
    pd.to_datetime(df['date']).dt.tz_localize(tz='Asia/Tokyo')
    self.dt = df.index.astype(np.int64)//10**9
    PlotWidgetの中で、以下の用に使用する
    pg.PlotWidget(axisItems={'bottom': TimeAxisItem(orientation='bottom')})
    '''
    def __init__(self, *args, **kwargs):
        super(TimeAxisItem, self).__init__(*args, **kwargs)
    
    def tickStrings(self, values, scale, spacing):
        # return [datetime.fromtimestamp(v).strftime('%Y %m/%d %H:%M') for v in values]
        return [datetime.fromtimestamp(v).strftime('%Y %m/%d') for v in values]
        '''
        フォーマットの例
        %Y：西暦 ( 4桁) の 10 進表記を表します。
        %m：0埋めした10進数で表記した月。
        %d：0埋めした10進数で表記した月中の日にち。
        %H：0埋めした10進数で表記した時 (24時間表記)。
        %I：0埋めした10進数で表記した時 (12時間表記)。
        %M：0埋めした10進数で表記した分。
        %S：0埋めした10進数で表記した秒。
        %b：ロケールの月名を短縮形で表示します。
        %B：ロケールの月名を表示します。
        
        詳細はこちら。
        https://docs.python.org/ja/3/library/datetime.html#strftime-and-strptime-behavior
        '''

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.init_ui()

        df = pd.read_csv('./blood_data_sorted.csv', index_col=0,usecols=[0,*range(2, 20)])
        self.df = df.set_index(pd.to_datetime(df.index, format='%Y-%m-%d'))
        self.dt = self.df.index.astype(np.int64)//10**9

        self.cols=df.columns
        self.num_of_cols = 5
        minx = self.dt[-30]
        maxx = self.dt[-1]

        self.set_graph_ui(self.cols, self.num_of_cols,minx,maxx)
        self.plot_region(self.num_of_cols)
        self.region.sigRegionChanged.connect(self.update_region_change)
        #self.region.sigRegionChanged.connect(lambda: self.update_region_change())
        self.region.setRegion([minx, maxx])
                

    def init_ui(self):
        # Windowサイズを設定
        self.setGeometry(100, 100, 2280, 1768)


    def plot_region(self, num_of_cols):
        setprop_region = lambda x: (x.setAutoVisible(y=True),
                                    x.enableAutoRange('y'),
                                    x.showAxis('right'),
                                    x.hideAxis('left'), 
                                    x.getAxis('right').setHeight(0))
        region = pg.LinearRegionItem() # http://www.pyqtgraph.org/documentation/graphicsItems/linearregionitem.html
        
        plt_region = self.graphicsView.addPlot(axisItems={'bottom': TimeAxisItem(orientation='bottom')},row=4,col=0, colspan=num_of_cols)
        plt_region.layout.setRowStretchFactor(4, 1)
        plt_region.addItem(region, ignoreBounds=True)
        setprop_region(plt_region)
        plt_region.plot(x=self.dt, y=self.df['血圧（最高）'])

        self.region = region
        
    def set_graph_ui(self,cols, num_of_cols, minx, maxx):
        # colsは、表示するデータの種類（以下のとおり）
        # '血圧（最高）', '血圧（最低）', '脈拍', 'ALT（GPT）', 'γ-GTP', '総蛋白TP', 'アルブミンALB', 'ALB/G', 'CHOL', 'GALB', 'RBC', 'Hb', 'Ht', 'MCV', 'MCH', 'MCHC', 'WBC', 'PLT'
        # 18種あります。
        #
        # num_of_colsは、表示するグラフのカラム数
        # minx,maxxは、初期表示のX軸の範囲
        graph_obj = []
        for i in range(len(cols)):
            graph_obj.append('p'+str(f"{i}"))

        # 折返し用に行数を算出
        if len(graph_obj) % num_of_cols == 0:
            num_of_rows = len(graph_obj)//num_of_cols
        else:
            num_of_rows = (len(graph_obj)//num_of_cols) + 1

        # レイアウト関連
        setprop = lambda x: (x.showGrid(x=True, y=True, alpha = 1),
                             x.enableAutoRange('y'),
                             x.addLegend(),
                             x.hideAxis('left'), 
                             x.getAxis('right').setHeight(0))


        self.graph_id_num = []
        for i in range(len(cols)):
            graph_obj[i] = self.graphicsView.addPlot(axisItems={'bottom': TimeAxisItem(orientation='bottom')})
            self.graph_id_num.append(id(graph_obj[i]))
            #graph_id.setXRange(*self.region.getRegion(), padding=0)
            graph_obj[i].setXRange(minx,maxx, padding=0)
            graph_label = cols[i]
            setprop(graph_obj[i])
            #graph_obj[i].setTitle('<font size=\'5\' color=\'#FFFFFF\'>'+ '献血結果' +'</font>')
            styles = {'color':'white','font-size':'20px', 'font-style':'bold'}
            graph_obj[i].setLabel('left', text=graph_label, units='', **styles)

            self.plot_xy(graph_label, graph_obj[i])
            graph_obj[i].layout.setRowStretchFactor(i, 15)
            if (i + 1) % num_of_cols == 0:
                self.graphicsView.nextRow()

    def draw_graph(self,cols,graph_id):
            upper = cols+'_upper'
            lower = cols+'_lower'
            cm2 = pg.colormap.get('Reds', source='matplotlib')# for example
            #cm = pg.colormap.get('CET-L19')
            #cm2 = pg.colormap.get('CET-L19')
            cm2.setMappingMode('MIRROR') # set mapping mode
            center_num = ((standard_data[cols][1]-standard_data[cols][0])/2)
            pen0 = cm2.getPen( span=(standard_data[cols][0], standard_data[cols][1]), width=2)
            brush0 = cm2.getBrush( span=(8,49),orientation='horizontal')
            #print(brush0)
            graph_id.addItem(pg.PlotDataItem(self.dt, self.df[cols], pen=pen0, symbol='o', symbolPen=pen0, symbolBrush=brush0,symbolSize=10))
            graph_id.addItem(pg.PlotDataItem(self.dt, self.df[cols].rolling(5).mean(), pen=pg.mkPen((255,255,255,208), width=5)))
            self.df[upper]=standard_data[cols][1]
            self.df[lower]=standard_data[cols][0]

            upper = pg.PlotDataItem(self.dt, self.df[upper], pen='g', symbol=None)
            lower = pg.PlotDataItem(self.dt, self.df[lower], pen='g', symbol=None)
            graph_id.addItem(upper)
            graph_id.addItem(lower)
            brushes = [0.5, (0,205,0, 30), 0.5]
            fills = pg.FillBetweenItem(upper, lower, brushes[1])
            fills.setZValue(-100)
            graph_id.addItem(fills)
            inf_upper = pg.InfiniteLine(movable=False, angle=0, pen=(0, 255, 0), hoverPen=(0,200,0),label='{value:0.2f} '+standard_data[cols][2])
            inf_lower = pg.InfiniteLine(movable=False, angle=0, pen=(0, 255, 0), hoverPen=(0,200,0),label='{value:0.2f} '+standard_data[cols][2])
            inf_upper.setPos(pg.Point(0, standard_data[cols][1]))
            inf_lower.setPos(pg.Point(0, standard_data[cols][0]))
            graph_id.addItem(inf_upper)
            graph_id.addItem(inf_lower)

    # データを扱うコードのみを記述
    def plot_xy(self, cols, graph_id):
        #s = self.df[cols]
        #s_rolling = self.df[cols].rolling(5).mean()
        if cols == 'GALB':        
            self.df['GALB_upper']=17
            graph_id.addItem(pg.PlotDataItem(self.dt, self.df['GALB_upper'], pen='r', symbol=None))
            graph_id.setYRange(10,17)
            inf_upper = pg.InfiniteLine(movable=False, angle=0, pen=(255, 0, 0), hoverPen=(0,200,0),label='{value:0.2f}%')
            inf_upper.setPos(pg.Point(0, 16.5))
            graph_id.addItem(inf_upper)
        
        elif cols == 'ALT（GPT）':
            self.draw_graph(cols,graph_id)

        elif cols == 'γ-GTP':
            self.draw_graph(cols,graph_id)
            
        elif cols == '総蛋白TP':
            self.draw_graph(cols,graph_id)
            
        elif cols == 'アルブミンALB':
            self.draw_graph(cols,graph_id)
            
        elif cols == 'ALB/G':
            self.draw_graph(cols,graph_id)
        
        elif cols == 'CHOL':
            self.draw_graph(cols,graph_id)
            
        elif cols == 'RBC':
            self.draw_graph(cols,graph_id)
            
        elif cols == 'Hb':
            self.draw_graph(cols,graph_id)
            
        elif cols == 'Ht':
            self.draw_graph(cols,graph_id)
            
        elif cols == 'MCV':
            self.draw_graph(cols,graph_id)
            
        elif cols == 'MCH':
            self.draw_graph(cols,graph_id)
            
        elif cols == 'MCHC':
            self.draw_graph(cols,graph_id)
            
        elif cols == 'MCHC':
            self.draw_graph(cols,graph_id)
            
        elif cols == 'WBC':
            self.draw_graph(cols,graph_id)
            
        elif cols == 'PLT':
            self.draw_graph(cols,graph_id)

        else:
            pass

        # 基準値 
        # 血圧（最高）
        # 血圧（最低）
        # 脈拍
        # 3 ALT（GPT）基準値: 8～49 IU/L
        # 4 γ-GTP 基準値: 9～68 IU/L
        # 5 '総蛋白TP', 総蛋白 TP 基準値: 6.6～8.2 g/dL
        # 6 'アルブミンALB', アルブミン ALB 基準値: 4.0～5.1 g/dL
        # 7 'ALB/G', アルブミン対グロブリン比 A/G 基準値: 1.3～2.1
        # 8 'CHOL', コレステロール CHOL 基準値: 140～259 mg/dL
        # 10 'RBC', 赤血球数 RBC 基準値(男性): 418～560 x10^4 /μL
        # 11 'Hb', ヘモグロビン量 Hb 基準値(男性): 12.7～17.0 g/dL
        # 12 'Ht', ヘマトクリット値 Ht 基準値(男性): 38.8～50.0 %
        # 13 'MCV', 平均赤血球容積 MCV 基準値: 83.0～99.5 fL
        # 14 'MCH', 平均赤血球ヘモグロビン量 MCH 基準値: 26.8～33.5 pg
        # 15 'MCHC', 平均赤血球ヘモグロビン濃度 MCHC 基準値: 31.7～35.2 %
        # 16 'WBC', 白血球数 WBC 基準値: 38～89 x10^2 /μL
        # 17 'PLT', 血小板数 PLT 基準値: 17.0～36.5 x10^4/μL 
        # 
        # このうち、cols[]が '血圧（最高）', '血圧（最低）', '脈拍'は、基準なし
        #
        # 'GALB'は、上限値のみ
        ## 9 グリコアルブミンGA 基準値: 16.5 % 未満
        #
        # ほかは、上下限値を記載
        # 'ALT（GPT）', 'γ-GTP', '総蛋白TP', 'アルブミンALB', 'ALB/G', 'CHOL', 'RBC', 'Hb', 'Ht', 'MCV', 'MCH', 'MCHC', 'WBC', 'PLT'
        # # 
        
    
    def update_region_change(self, region):
        #self.graphicsView.clear()
        import _ctypes
        for case in range(len(self.graph_id_num)):
            _ctypes.PyObj_FromPtr(self.graph_id_num[case]).setXRange(*self.region.getRegion(), padding=0)
        region.setZValue(10)
        
        #print(minx,maxx)
        #self.plot_xy(self.cols, self.num_of_cols,minx, maxx)


    def update_region(self, window, viewRange):
        self.region.setRegion(viewRange[0])

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()

if __name__ == '__main__':
    main()