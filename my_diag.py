#!/usr/bin/env python3
from PyQt5 import QtCore
import rospy
from apscheduler.schedulers.background import BackgroundScheduler
from diagnostic_msgs.msg import DiagnosticStatus, KeyValue
#from  msu_msgs import BoschRadarTarget
import subprocess
from PyQt5 import Qt
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial
import sys
import random
import time
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
#diagnostic listener
rol_cntr = 0
diag_data = {"front_radar_LOC":'no data received',"front_radar_sgu_fail":'no data received',"front_radar_hw_fail":'no data received',"mabx":'no data received', 'mobileye':'no data received','MK5_comm':'no data received'}
#bosch_target_x = []

def front_radar_callback(data):
    #rospy.loginfo(rospy.get_caller_id() + 'I heard %s', data.data)
    #print('front_radar: ',data.values['LOC'])
    #diag_data['front_radar'] = data.values
    diag_data['front_radar_LOC'] = data.values[0].value
    diag_data['front_radar_sgu_fail'] = data.values[2].value
    diag_data['front_radar_hw_fail'] = data.values[3].value
    
def mabx_callback(data):
    #rospy.loginfo(rospy.get_caller_id() + 'I heard %s', data.data)
    #print('mabx; ',data.value)
    diag_data['mabx'] = data.value

def mobileye_callback(data):
    #print('mobileye: ',data.value)
    diag_data['mobileye'] = data.value
    #print(diag_data)

# def bosch_callback(data):
#     bosch_target_x.append(data.value)

def ping_mk5():
    #ping mk5 to check connection
    try:
        subprocess.check_output(["ping", "-c", "1", "195.0.0.125"])
        diag_data['MK5_comm'] = "Ok"                     
    except subprocess.CalledProcessError:
        diag_data['MK5_comm'] = "Loss_comm"

def print_diag_data(cav_diag_ui):
    global rol_cntr
    #print(diag_data)    
    subprocess.run(['clear'])

    for k,v in diag_data.items():
        if k == 'front_radar':
            #print(type(v[0]))
            print("LOC: ", v[0].value)
            print("sgu_fail: ", v[2].value)
            print("hw_fail: ", v[3].value)
            #print(k+': ',v)
        else:
            print(k+': ',v)
            #print(type(v))
            cav_diag_ui.diag_data_field[k].setText(v)
    #print(bosch_target_x)
    if (rol_cntr > 10):
        rol_cntr = 0
    print("rolling counter: ",rol_cntr)
    rol_cntr += 1

def listener():

    # In ROS, nodes are uniquely named. If two nodes with the same
    # name are launched, the previous one is kicked off. The
    # anonymous=True flag means that rospy will choose a unique
    # name for our 'listener' node so that multiple listeners can
    # run simultaneously.
    rospy.init_node('listener', anonymous=True)

    rospy.Subscriber('front_radar_diagnostics', DiagnosticStatus, front_radar_callback)
    rospy.Subscriber('mabx_loc_status', KeyValue, mabx_callback)
    rospy.Subscriber('mobileye_loc_status', KeyValue, mobileye_callback)
    #rospy.Subscriber('front_radar_targets', BoschRadarTarget, bosch_callback)

    Cavapp = QApplication(sys.argv)
    Cavapp.setStyle('Fusion')
    car_ui = CavUI()
    scheduler = BackgroundScheduler()    
    scheduler.start()
    scheduler.add_job(ping_mk5,'interval',seconds=1)
    scheduler.add_job(partial(print_diag_data,car_ui),'interval',seconds=1)

    sys.exit(Cavapp.exec())

    # spin() simply keeps python from exiting until this node is stopped
    #rospy.spin()

#UI
class CavUI(QMainWindow):
    ''' 
    '''

    def __init__(self):
        super().__init__()
        self.setWindowTitle('CAV UI')
        #self.setFixedSize(400,400)
        self.setGeometry(50,50,1500,900)
        self._generalLayout = QGridLayout()
        self._centralWidget = QWidget(self)
        self.setCentralWidget(self._centralWidget)
        self._centralWidget.setLayout(self._generalLayout)
        self._createDisplay1()
        self._createDisplay2()
        self._createDisplay3()
        self._createDisplay4()
        #self._createButtons()
        self.show()
        #self.threadpool = QThreadPool()
        
    
    def _createDisplay1(self):
        dispLayout = QVBoxLayout()
        display_label = QLabel('Birds-eye-view')
        display_label.setFont(QFont('Arial', 14))
        dispLayout.addWidget(display_label)
        self._generalLayout.addLayout(dispLayout,1,1)

    def _createDisplay2(self):
        cav_dispLayout = QVBoxLayout()
        cav_dispLayout.setContentsMargins(10,10,10,10)

        cav_display_label = QLabel('CAv diagnostic')
        cav_display_label.setFont(QFont('Arial', 14))
        cav_dispLayout.addWidget(cav_display_label,alignment=Qt.AlignTop)
        cav_dispLayout.addItem(QSpacerItem(500,20,QSizePolicy.Fixed,QSizePolicy.Fixed))
        self.diag_data_field = {}
        for k,v in diag_data.items():
            text_label = QLabel(k)
            text_label.setFont(QFont('Arial',11))
            cav_dispLayout.addWidget(text_label,alignment=Qt.AlignTop)
            cav_dispLayout.addItem(QSpacerItem(500,5,QSizePolicy.Fixed,QSizePolicy.Fixed))
            self.diag_data_field[k] = QLineEdit(v)
            self.diag_data_field[k].setFixedWidth(500)
            self.diag_data_field[k].setFont(QFont('Arial',11))
            cav_dispLayout.addWidget(self.diag_data_field[k],alignment=Qt.AlignTop)
            cav_dispLayout.addItem(QSpacerItem(500,10,QSizePolicy.Fixed,QSizePolicy.Fixed))
        
        self._generalLayout.addLayout(cav_dispLayout,2,1)

    def _createDisplay3(self):
        dispLayout = QVBoxLayout()
        display_label = QLabel('PCM... space')
        display_label.setFont(QFont('Arial', 14))
        dispLayout.addWidget(display_label)
        self._generalLayout.addLayout(dispLayout,1,2)

    def _createDisplay4(self):
        dispLayout = QVBoxLayout()
        display_label = QLabel('vehicle rpm')
        display_label.setFont(QFont('Arial', 14))
        dispLayout.addWidget(display_label)

        self.rpm_canvas = MplCanvas(self,width=5,height=4,dpi=100)
        dispLayout.addWidget(self.rpm_canvas)

        n_data = 50
        self.xdata = list(range(n_data))
        self.ydata = [0 for i in range(n_data)]
        self._plot_ref = None
        self.update_plot()
        self.show()
        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

        self._generalLayout.addLayout(dispLayout,2,2)

    def update_plot(self):
        self.ydata = self.ydata[1:]+[random.randint(0,10)]
        if self._plot_ref is None:
            plot_refs = self.rpm_canvas.axes.plot(self.xdata,self.ydata)
            self._plot_ref = plot_refs[0]
        else:
            self._plot_ref.set_ydata(self.ydata)
        self.rpm_canvas.axes.autoscale(True)
        self.rpm_canvas.draw()


class MplCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)
    

if __name__ == '__main__':
    
    listener()


    
    