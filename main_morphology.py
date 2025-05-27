from PyQt5.QtWidgets import *
from PyQt5.Qt import Qt
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import pyqtSignal
import sys
from wisdom_store.ui.main.Ui_Morphology import Ui_Morphology
import wisdom_store.ui.main.resources_rc
from wisdom_store.wins.main_foldingbar_item import FoldingBarItem
from wisdom_store.wins.main_dialog import Dialog


class Morphology(FoldingBarItem):
    # 定义单独的信号
    TargetTypeChanged = pyqtSignal(str)
    OperationTypeChanged = pyqtSignal(str)
    ParameterChanged = pyqtSignal(int)
    MorphologyReset = pyqtSignal()

    def __init__(self, parent):
        super(Morphology, self).__init__()
        self.parent = parent

        # 初始化窗口
        self.win = QWidget()
        self.mainWin = Ui_Morphology()
        self.mainWin.setupUi(self.win)
        self.set_content(self.win)
        self.set_title("形态学变换")

        # 隐藏系统默认框架
        self.setWindowFlags(Qt.FramelessWindowHint)

        # 设置鼠标追踪
        self.setMouseTracking(True)

        # 初始化操作类型下拉框
        self.mainWin.comboBoxOperationType.clear()
        operations = ["无", "膨胀", "腐蚀", "开运算", "闭运算", "小区域删除", "骨架化", "去枝权"]
        for op in operations:
            self.mainWin.comboBoxOperationType.addItem(op)

        # 事件绑定
        self.signalConnect()

        # 控件状态初始化
        self.stateInit()

    def signalConnect(self):
        self.mainWin.pBtnApplyMorphological.clicked.connect(self.confirm) #应用形态学变换
        self.mainWin.comboBoxTargetType.currentTextChanged.connect(self.onTargetTypeChanged)
        self.mainWin.comboBoxOperationType.currentTextChanged.connect(self.onOperationTypeChanged)
        self.mainWin.comboBoxTargetType.currentTextChanged.connect(self.parent.check_morphology_conditions_and_show)
        self.mainWin.sliderParameterName.valueChanged.connect(self.onParameterChanged)

    def stateInit(self):
        self.targetType = ""
        self.operationType = "无"
        self.parameterValue = 1
        self.toSave = False

    def show(self) -> None:
        self.project = self.parent.project  # parent is MainWin
        # 初始化目标类型下拉框
        self.mainWin.comboBoxTargetType.clear()
        if self.project and hasattr(self.project, 'classes'):
            for cls_data in self.project.classes:  # Assuming classes is a list of dicts with 'type'
                self.mainWin.comboBoxTargetType.addItem(cls_data['type'])

        # Enable/disable based on conditions
        self.parent.check_morphology_conditions_and_show()  # Call MainWin's check

        # Resetting UI to defaults should happen after check, or be part of check
        # self.reset() # reset might disable things again if called before check
        super().show()  # Call super().show() after internal setup
        # If reset is needed, ensure it respects the enabled state from check_morphology_conditions_and_show
        if self.mainWin.comboBoxTargetType.count() > 0:
            if not self.targetType:  # If targetType not set, default to first
                self.mainWin.comboBoxTargetType.setCurrentIndex(0)
                self.onTargetTypeChanged(self.mainWin.comboBoxTargetType.currentText())
        else:  # No types, definitely disable
            self.win.setEnabled(False)
            self.mainWin.comboBoxOperationType.setEnabled(False)
            self.mainWin.sliderParameterName.setEnabled(False)
            self.mainWin.pBtnApplyMorphological.setEnabled(False)

        # If still "无", ensure slider is set to a sensible default
        if self.mainWin.comboBoxOperationType.currentText() == "无":
            self.mainWin.sliderParameterName.setValue(1)
            self.updateParamValue()

    def hide(self) -> None:
        if not self.toSave:
            self.cancel()
        return super().hide()

    def update_parameter_name(self):
        current_operation = self.mainWin.comboBoxOperationType.currentText()
        base_text = "参数名："
        min_val, max_val, current_val = 1, 10, 1

        if current_operation in ["膨胀", "腐蚀", "开运算", "闭运算", "去枝杈"]:  # Corrected 去枝杈
            base_text = "迭代次数："
            min_val, max_val, current_val = 1, 10, 1  # Example range
        elif current_operation == "小区域删除":
            base_text = "区域大小："
            min_val, max_val, current_val = 1, 1000, 1  # Example range
        elif current_operation == "骨架化":
            base_text = "骨架宽度："
            min_val, max_val, current_val = 1, 10, 1  # Example range for thickening

        self.mainWin.sliderParameterName.setMinimum(min_val)
        self.mainWin.sliderParameterName.setMaximum(max_val)

        # Try to keep existing value if in new range, else set to default for op
        if min_val <= self.parameterValue <= max_val:
            self.mainWin.sliderParameterName.setValue(self.parameterValue)
        else:
            self.mainWin.sliderParameterName.setValue(current_val)
            self.parameterValue = current_val  # Update internal state

        self.mainWin.labelParameterName.setText(f"{base_text}")  # Just the name
        self.mainWin.labelParameterNameMin.setText(str(min_val))
        self.mainWin.labelParameterNameMax.setText(str(max_val))
        # The slider's valueChanged signal will call onParameterChanged -> updateParamValue
        # So we don't need to set the text with value here directly.
        # Force an update of the displayed value if the slider didn't change but its meaning did
        self.updateParamValue()


    def updateParamValue(self):
        self.parameterValue = self.mainWin.sliderParameterName.value()
        self.ParameterChanged.emit(self.parameterValue)

    def onTargetTypeChanged(self, targetType):
        self.targetType = targetType
        self.TargetTypeChanged.emit(targetType)

    def onOperationTypeChanged(self, operationType):
        self.operationType = operationType
        self.update_parameter_name()
        self.OperationTypeChanged.emit(operationType)
        self.parent.check_morphology_condictions_and_show()

    def onParameterChanged(self, value):
        self.parameterValue = value
        self.updateParamValue()

    def confirm(self):
        self.toSave = True
        if self.operationType == "无":
            self.MorphologyReset.emit()
        else:
            self.parent.MainGraphicsView.confirmMorphologyApplication()

        self.hide()
        self.reset()

    def reset(self):
        if self.mainWin.comboBoxTargetType.count() > 0:
            pass
        self.mainWin.comboBoxOperationType.setCurrentIndex(0)  # "无"
        self.onOperationTypeChanged("无")
        self.MorphologyReset.emit()
        self.toSave = False


    def cancel(self):
        self.MorphologyReset.emit()
        self.reset()
        self.toSave = False

    def resetParameters(self):
        self.reset()

    def trans(self):
        if len(self.parent.project.classes) == 0:
            self.ui.toolButtonFold.setChecked(False)
            dlg = Dialog('请先在编辑-设定目标类型中设置标签')
            dlg.exec()
            self.parent.ui.tBtnArrow.click()
            return
        elif len(self.parent.fileList) == 0:
            self.ui.toolButtonFold.setChecked(False)
            dlg = Dialog('请先添加图片')
            dlg.exec()
            self.parent.ui.tBtnArrow.click()
            return
        if self.ui.toolButtonFold.isChecked():
            self.ui.widgetMain.setVisible(True)
            self.ui.toolButtonFold.setToolTip(QtCore.QCoreApplication.translate("Main", "折叠"))
            if self.win:
                self.ui.scrollArea.setWidget(self.win)
                self.show()
                self.parent.check_morphology_conditions_and_show()
        else:
            self.cancel()
            self.ui.widgetMain.setVisible(False)
            self.ui.toolButtonFold.setToolTip(QtCore.QCoreApplication.translate("Main", "展开"))


if __name__ == '__main__':
    QtCore.QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QtGui.QGuiApplication.setAttribute(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    myWin = Morphology(None)
    myWin.show()
    sys.exit(app.exec_())