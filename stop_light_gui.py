from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial
import traceback, sys
import paramiko
import time


class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    progress
        int indicating % progress

    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)

class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super().__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done

class StopLightUI(QMainWindow):
    ''' the ui consist of buttons for the pattern and the display of which pattern is playing
        amd the display for indicating the pattern has finished playing
    '''
    pattern_command_dict = {'Pattern 1': 'ls', 'Pattern 2':'pwd', 'Pattern 3':'echo LOLOLOL'}

    def __init__(self):
        super().__init__()
        self.setWindowTitle('StopLight')
        #self.setFixedSize(400,400)
        self.setGeometry(50,50,400,400)
        self._generalLayout = QVBoxLayout()
        self._centralWidget = QWidget(self)
        self.setCentralWidget(self._centralWidget)
        self._centralWidget.setLayout(self._generalLayout)
        self._createDisplay()
        self._createButtons()
        self.show()
        self.threadpool = QThreadPool()
        
    
    def _createDisplay(self):
        dispLayout = QVBoxLayout()
        display_label = QLabel('now playing:')
        display_label.setFixedHeight(35)
        dispLayout.addWidget(display_label)
        self._display_pattern = QLineEdit()
        self._display_pattern.setFixedHeight(35)
        self._display_pattern.setAlignment(Qt.AlignLeft)
        dispLayout.addWidget(self._display_pattern)
        stat_label = QLabel('status:')
        stat_label.setFixedHeight(35)
        dispLayout.addWidget(stat_label)
        self._stat = QLineEdit()
        self._stat.setFixedHeight(35)
        self._stat.setAlignment(Qt.AlignLeft)
        dispLayout.addWidget(self._stat)
        #self.pbar = QProgressBar(self)
        #dispLayout.addWidget(self.pbar)
        #self.pbar.setValue(50)

        self._generalLayout.addLayout(dispLayout)
    
    def _createButtons(self):
        self._buttons = {}
        buttonsLayout = QVBoxLayout()
        list_buttons = ['Pattern 1',
                   'Pattern 2',
                   'Pattern 3']
        for btnText in range(len(list_buttons)):
            self._buttons[list_buttons[btnText]] = QPushButton(list_buttons[btnText])
            self._buttons[list_buttons[btnText]].clicked.connect(partial(self.setDisplayText, list_buttons[btnText]))
            self._buttons[list_buttons[btnText]].clicked.connect(partial(self.setStatText, ''))
            buttonsLayout.addWidget(self._buttons[list_buttons[btnText]])
        self._send_button = QPushButton('send')
        self._send_button.setMinimumHeight(40)
        self._send_button.pressed.connect(self.create_worker)
        self._send_button.pressed.connect(partial(self.setStatText,'running'))
        buttonsLayout.addWidget(self._send_button)
        self._generalLayout.addLayout(buttonsLayout)
    
    def setDisplayText(self,text):
        self._display_pattern.setText(text)
        print(self.displayText())
        #self.display_pattern.setFocus()

    def displayText(self):
        return self._display_pattern.text()

    def setStatText(self,txt):
        self._stat.setText(txt)

    # def execute_this_fn(self, progress_callback):
    #     for n in range(0, 5):
    #         time.sleep(1)
    #         progress_callback.emit(n*100/4)
    #    return "Done."

    def print_output(self, s):
        print(s)

    def thread_complete(self):
        print("Pattern COMPLETE!")
        self.setStatText('finish')
        self.setDisplayText('')
    
    #ssh to send pattern
    def send_pattern_fn(self, pattern):
        print('start sending')
        host = '192.168.0.4'
        username = 'joshjet'
        password = 'jet12345'
        port = 22
        cmd = self.pattern_command_dict[pattern]
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port, username, password)
        stdin, stdout, stderr = ssh.exec_command(cmd)
        stdin.close()
        #print(stdout.readlines())
        msg = stdout.readlines()
        stdout.close()
        stderr.close()

        return msg
        
    def create_worker(self):
        # Pass the function to execute
        pat_2_send = self.displayText()
        worker = Worker(self.send_pattern_fn,pat_2_send) # Any other args, kwargs are passed to the run function
        worker.signals.result.connect(self.print_output)
        worker.signals.finished.connect(self.thread_complete)

        self.threadpool.start(worker)

    

if __name__ == '__main__':
    StopLight = QApplication(sys.argv)
    window = StopLightUI()
    sys.exit(StopLight.exec())