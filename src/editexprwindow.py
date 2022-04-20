from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
import nuke
import json, os, re, base64, copy


class BrickerEditRegexDialog(QWidget):
    def __init__(self, node=None):
        super(BrickerEditRegexDialog, self).__init__(getMainWindow())
        self.node = node
        self.build_ui()
        self.setMaximumWidth(800)
        self.setWindowFlags(Qt.Tool)
        if self.node:
            self.setWindowTitle('Edit extract expression (%s)' % node.name())
        else:
            self.setWindowTitle('Edit extract expression')
        self.expression_te.setWordWrapMode(QTextOption.NoWrap)
        metrics = QFontMetrics(self.font())
        self.expression_te.setTabStopWidth(4 * metrics.width(' '))

        self.help_btn.clicked.connect(self.help)
        self.preset_btn.clicked.connect(self.presets_menu)
        self.python_rb.clicked.connect(self.update_ui)
        self.tcl_rb.clicked.connect(self.update_ui)
        self.regex_rb.clicked.connect(self.update_ui)
        self.expression_te.textChanged.connect(self.compute_test)
        # self.test_input_le.textChanged.connect(self.compute_test)
        self.group_spb.valueChanged.connect(self.compute_test)
        self.save_btn.clicked.connect(self.save_to_node)
        self.help_btn.hide()
        self.load_from_node()

    def _read_ui(self):
        expression = self.expression_te.toPlainText()
        if not expression:
            return
        lang = 'py' if self.python_rb.isChecked() else (
            'tcl' if self.tcl_rb.isChecked() else 're'
        )
        data = dict(
            expr=expression,
            lang=lang
        )
        if lang == 're':
            data['expr'] = data['expr'].replace('\\', '\\\\')
            data['group'] = self.group_spb.value()
        return data

    def dumps(self):
        data = self._read_ui()
        if data:
            return base64.encodestring(json.dumps(data))

    @staticmethod
    def loads(node):
        k = node.knob('extractexpr')
        if k:
            v = k.getValue()
            if not v:
                return
            try:
                data = json.loads(base64.decodestring(v))
                return data
            except Exception as e:
                print('ERROR:', str(e), v)
                k.setValue('')
                return

    def load_from_node(self):
        data = self.loads(self.node) or {}
        self.apply_preset(data)

    def save_to_node(self):
        data = self.dumps()
        if data:
            self.node.knob('extractexpr').setValue(data)
        else:
            self.node.knob('extractexpr').setValue('')

    def apply_preset(self, data):
        self.expression_te.setPlainText(data.get('expr', ''))
        if data.get('lang') == 'py':
            self.python_rb.setChecked(1)
        elif data.get('lang') == 're':
            data['expr'] = data['expr'].replace('\\\\', '\\')
            self.regex_rb.setChecked(1)
            self.group_spb.setValue(data.get('group', 0))
        elif data.get('lang') == 'tcl':
            self.tcl_rb.setChecked(1)
        self.update_ui()

    def update_ui(self):
        if self.regex_rb.isChecked():
            self.help_lb.setText('Using "file" knob from input node')
            self.tst_wd.show()
        elif self.tcl_rb.isChecked():
            self.tst_wd.hide()
            self.help_lb.setText('Use "thisNode" as current input node in cycle')
        else:
            self.help_lb.setText('Use "thisNode" as current input Python node in cycle')
            self.tst_wd.hide()
        self.compute_test()

    def compute_test(self):
        data = self._read_ui()
        error = None
        result = None
        node = None
        if not data:
            return
        if not data['expr']:
            self.result_le.setText('')
            return
        if self.node.inputs():
            nodes = [self.node.input(x) for x in range(self.node.inputs())]
            node = ([x for x in nodes if x] or [None])[0]
            if not node:
                error = 'no input nodes'
        else:
            error = 'no input nodes'
        if not error and node:
            result, error = self.evaluate_expression(data['lang'],
                                                     data['expr'],
                                                     node,
                                                     data.get('group'))

        if result:
            self.result_le.setText(self.__split_message(str(result)))
        else:
            self.result_le.setText('')
        if error:
            self.result_le.setText('ERROR: %s' % self.__split_message(str(error)))

    @staticmethod
    def evaluate_expression(lang, expr, node, regex_group=None):
        res = None
        err = None

        if lang == 'py':
            expr = expr.strip().replace('thisNode', 'nuke.toNode("%s")' % node.fullName())
            f = r'''\
def _pyfunc():
{}
_result = _pyfunc()
'''
            ns = dict(
                nuke=nuke,
                os=os,
                re=re
            )
            if len(expr.split('\n')) == 1:
                expr = 'return '+expr
            else:
                if 'return' not in expr:
                    err = 'you should return value from multi line expression'
            func = f.format(
                ''.join(['    ' + x + '\n' for x in expr.split('\n')])
            )
            try:
                exec(func, ns)
                res = ns['_result']
            except Exception as e:
                err = str(e)

        elif lang == 're':
            test_line = None
            k = node.knob('file')
            if not k:
                err = 'knob "file" not found'
            else:
                test_line = k.evaluate()
            if not err and test_line is not None:
                try:
                    m = re.match(expr.replace('\\\\', '\\'), test_line)
                    if m:
                        if not regex_group is None:
                            try:
                                res = m.group(regex_group)
                            except Exception as e:
                                err = str(e)
                        else:
                            res = m.group(0)
                    else:
                        m = re.findall(expr.replace('\\\\', '\\'), test_line)
                        if m:
                            res = m[0]
                        else:
                            err = 'no match'
                except Exception as e:
                    err = str(e)

        elif lang == 'tcl':
            exp = expr.replace('thisNode', node.fullName()) \
                .replace('\n', ' ')
            try:
                res = nuke.tcl(str(exp))
            except Exception as e:
                err = str(e)
        return res, err

    def __split_message(self, msg):
        maxlen = 200
        if len(msg) > maxlen:
            return str(msg)[:200] + '...'
        else:
            return msg

    def get_presets(self):
        dp = copy.deepcopy(default_presets)
        f = self.presets_folder()
        if f:
            for file in os.listdir(f):
                full = os.path.join(f, file)
                if os.path.isfile(full):
                    try:
                        pr = json.load(open(full))
                    except:
                        continue
                    if pr.get('lang') == 're':
                        dp['regex'].append(pr)
                    elif pr.get('lang') == 'py':
                        dp['python'].append(pr)
                    else:
                        dp['tcl'].append(pr)
        return dp

    def presets_menu(self):
        presets = self.get_presets()
        menu = QMenu()
        regmenu = QMenu('Regex')
        menu.addMenu(regmenu)
        tclmenu = QMenu('TCL')
        menu.addMenu(tclmenu)
        pymenu = QMenu('Python')
        menu.addMenu(pymenu)
        menu.addSeparator()
        menu.addAction(QAction('Save current as...', self, triggered=self.save_current_preset))
        menu.addAction(QAction('Open presets folder...', self, triggered=self.open_preset_folder))

        if presets.get('regex'):
            for p in presets.get('regex'):
                p['lang'] = 're'
                regmenu.addAction(QAction(p['title'], self, triggered=lambda x=p: self.apply_preset(x)))
        else:
            act = QAction('Empty', self)
            act.setEnabled(0)
            regmenu.addAction(act)

        if presets.get('tcl'):
            for p in presets.get('tcl'):
                p['lang'] = 'tcl'
                tclmenu.addAction(QAction(p['title'], self, triggered=lambda x=p: self.apply_preset(x)))
        else:
            act = QAction('Empty', self)
            act.setEnabled(0)
            tclmenu.addAction(act)

        if presets.get('python'):
            for p in presets.get('python'):
                p['lang'] = 'py'
                pymenu.addAction(QAction(p['title'], self, triggered=lambda x=p: self.apply_preset(x)))
        else:
            act = QAction('Empty', self)
            act.setEnabled(0)
            pymenu.addAction(act)
        menu.exec_(QCursor.pos())

    def help(self):
        print('HELP!!!')

    def build_ui(self):
        self.ly1 = QVBoxLayout(self)
        self.groupBox_3 = QGroupBox(self)
        self.ly2 = QVBoxLayout(self.groupBox_3)
        self.ly3 = QHBoxLayout()
        self.regex_rb = QRadioButton('Regex')
        self.regex_rb.setChecked(True)
        self.ly3.addWidget(self.regex_rb)
        self.tcl_rb = QRadioButton('TCL')
        self.ly3.addWidget(self.tcl_rb)
        self.python_rb = QRadioButton('Python')
        self.ly3.addWidget(self.python_rb)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.ly3.addItem(spacerItem)
        self.preset_btn = QPushButton('Presets')
        self.preset_btn.setMaximumSize(QSize(50, 16777215))
        self.ly3.addWidget(self.preset_btn)
        self.help_btn = QPushButton('?')
        self.help_btn.setMaximumSize(QSize(20, 16777215))
        self.ly3.addWidget(self.help_btn)
        self.ly2.addLayout(self.ly3)
        self.help_lb = QLabel()
        self.ly2.addWidget(self.help_lb)
        self.expression_te = QPlainTextEdit(self.groupBox_3)
        self.ly2.addWidget(self.expression_te)
        self.grp_wd = QWidget(self.groupBox_3)
        self.ly2.addWidget(self.grp_wd)
        self.ly1.addWidget(self.groupBox_3)

        self.groupBox = QGroupBox(self)
        self.groupBox.setTitle("Result")
        self.ly5 = QVBoxLayout(self.groupBox)
        self.ly6 = QHBoxLayout()
        self.tst_wd = QWidget()
        tst_ly = QHBoxLayout()
        tst_ly.setContentsMargins(0,0,0,0)
        self.tst_wd.setLayout(tst_ly)
        # self.test_input_le = QLineEdit(self.groupBox)
        # self.test_input_le.setPlaceholderText('Regex test string')
        # tst_ly.addWidget(self.test_input_le)
        label = QLabel('Regex Group')
        tst_ly.addWidget(label)
        self.group_spb = QSpinBox(self.groupBox)
        tst_ly.addWidget(self.group_spb)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        tst_ly.addItem(spacerItem)

        self.ly5.addWidget(self.tst_wd)

        self.result_le = QLabel(self.groupBox)
        self.result_le.setText("")
        self.ly5.addWidget(self.result_le)
        self.ly1.addWidget(self.groupBox)
        self.save_btn = QPushButton('Save')
        self.ly1.addWidget(self.save_btn)

        self.groupBox_3.setTitle("Expression")
        self.resize(500, 400)

        self.help_lb.setText('Using "file" knob from input node')

    @classmethod
    def presets_folder(cls):
        f = os.path.expanduser('~/.pw_bricker_expression_presets')
        if not os.path.exists(f):
            try:
                os.makedirs(f)
            except:
                return
        return f

    @staticmethod
    def checkLegalChar(string):
        return re.sub('[^A-Za-z0-9]+', '_', string).lower()

    def open_preset_folder(self):
        f = self.presets_folder()
        if not f:
            QMessageBox.critical(self, 'Error', 'Cant create folder')
            return
        systems = {
            'nt': os.startfile,
            'posix': lambda foldername: os.system('xdg-open "%s"' % foldername),
            'os2': lambda foldername: os.system('open "%s"' % foldername)
        }
        systems.get(os.name, os.startfile)(f)

    def save_current_preset(self):
        text, ok = QInputDialog.getText(self, 'Save Preset', 'Enter Preset Name')
        if not ok:
            return
        name = self.checkLegalChar(text)
        if len(set(name)) == 1:
            QMessageBox.critical(self, 'Error', 'Wrong name')
            return
        folder = self.presets_folder()
        if not folder:
            QMessageBox.critical(self, 'Error', 'Cant get presets folder')
            return
        preset_file = os.path.join(folder, name+'.json')
        if os.path.exists(preset_file):
            QMessageBox.critical(self, 'Error', 'That name already exists')
            return
        data = dict(
            lang='re' if self.regex_rb.isChecked() else ('tcl' if self.tcl_rb.isChecked() else 'py'),
            expr=self.expression_te.toPlainText(),
            title=text
        )
        try:
            json.dump(data, open(preset_file, 'w'), indent=2)
        except:
            QMessageBox.critical(self, 'Error', "Can't save preset")

default_presets = dict(
    python=[dict(
                title='File Name',
                expr=r"os.path.basename(thisNode['file'].evaluate())"
                ),
            dict(
                title='File Name (Deep search)',
                expr=r"""def get_dep(node):
    d = node.dependencies()
    if len(d) == 1:
        return d[0]
if thisNode.knob('file'):
    return os.path.basename(thisNode.knob('file').evaluate())
else:
    dep = get_dep(thisNode)
    if dep.knob('file'):
        return os.path.basename(dep.knob('file').evaluate())
    while dep:
        dep = get_dep(dep)
        if not dep:
            break
        if dep.knob('file'):
            return os.path.basename(dep.knob('file').evaluate())
"""
                ),

    ],

    tcl=[dict(
                title='File Name',
                expr=r"basename  [value thisNode.file]"
                )
    ],

    regex=[dict(
                title='File name',
                expr=r'.*?([a-zA-Z0-9%_]+).\w{3}$',
                group=1
                ),
    ]
)


def getMainWindow():
    qApp = QApplication.instance()
    for widget in qApp.topLevelWidgets():
        if widget.metaObject().className() == 'Foundry::UI::DockMainWindow':
            return widget

# if nuke.thisKnob().name() == 'editexpr':
#     bricker_edit_expression_dialog = BrickerEditRegexDialog(nuke.thisNode())
#     bricker_edit_expression_dialog.show()

