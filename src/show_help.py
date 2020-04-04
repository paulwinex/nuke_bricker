from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
import webbrowser

class BrickerHelpDialog(QWidget):
    def __init__(self):
        super(BrickerHelpDialog, self).__init__(getMainWindow())
        self.ly = QVBoxLayout()
        self.setLayout(self.ly)
        self.setWindowFlags(Qt.Tool)
        self.setWindowTitle('pw Bricker Help')
        self.text = QTextBrowser()
        def ss(text):
            webbrowser.open(text.toString())
        self.text.setSource = ss
        self.ly.addWidget(self.text)

        if not 'brickerExistsVar' in __import__('__main__').__dict__:
            warn = '<h2><b style="color:red" >Bricker not installed!</b></h2>'
        else:
            warn=''


        self.text.setHtml(html.format(warn=warn))

        self.resize(570, 430)




html = '''{warn}<h1>Bricker Gizmo</h1>
<h3>by paulwinex 2017</h3>
<a style="color: darkgray;" href="http://paulwinex.com">www.paulwinex.com</a>
<h2><a style="color: darkgray;" href=" http://paulwinex.com/nuke-bricker/">Open Manual</a></h2>
<hr>
<div>
<h2>Install</h2>
  <ol>
    <li>Copy pw_bricker.gizmo and bricker.png to the Nuke Plugin Path</li>
    <li>Add this code to "menu.py" and restart Nuke:</li>
  </ol>
<div style="border: solid 1px">
<hr>
<code>
import nuke<br>
toolbar = nuke.toolbar("Nodes")<br>
toolbar.addCommand( "Merge/Bricker", "nuke.createNode('pw_bricker')", icon="bricker.png")<br>
def install_bricker():<br>
&nbsp;&nbsp;&nbsp;&nbsp;nuke.thisNode()['mainScript'].execute()<br>
&nbsp;&nbsp;&nbsp;&nbsp;nuke.removeOnCreate(install_bricker, nodeClass='pw_bricker')<br>
nuke.addOnCreate(install_bricker, nodeClass='pw_bricker')<br>
#fix overlay action<br>
nuke.menu('Viewer').items()[1].action().setChecked(True)
</code>
</div>
<hr>
<h2>Regex Helper</h2>
<b><a style="color: darkgray;" href="http://www.exlab.net/files/tools/sheets/regexp/regexp.png">RUS</a></b> or <b><a style="color: darkgray;" href="http://www.cheat-sheets.org/saved-copy/regular_expressions_cheat_sheet.png">ENG</a></b>
'''
def getMainWindow():
    qApp = QApplication.instance()
    for widget in qApp.topLevelWidgets():
        if widget.metaObject().className() == 'Foundry::UI::DockMainWindow':
            return widget

w = BrickerHelpDialog()
w.show()