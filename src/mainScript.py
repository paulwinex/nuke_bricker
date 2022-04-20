# Script for menu.py
# pwMenu = toolbar.addMenu("PW Tools")
# pwMenu.addCommand("Bricker", "nuke.createNode(\"pw_bricker\")")
# def install_bricker():
#     n = nuke.thisNode()
#     if n.Class() == 'pw_bricker':
#         n['mainScript'].execute()
#         nuke.removeOnCreate(install_bricker)
# nuke.addOnCreate(install_bricker)
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

import nuke, nukescripts
import nuke.rotopaint as rp
from PySide2.QtCore import *
from PySide2.QtGui import *
import re, math, os, json, webbrowser

################## VARIABLES

pwbr_objName = 'brickerTables'
pwbr_className = 'pw_bricker'
pwbr_detectKnob = 'brickedknobinfo'
brickerExistsVar = 'brickerInstalled'
pwbr_prefKnob = 'pw_bricker_pref'
pwbr_prefKnobTab1 = pwbr_prefKnob + '_start'
pwbr_prefKnobTab2 = pwbr_prefKnob + '_end'
pwbr_currentFrameKnobName = 'showframe'
pwbr_setFrameLabel = 'HLD'
pwbr_offsetFrameLabel = 'OFS'
pwbr_fontFactor = 0.7
pwbr_leading = 0.2
pwbr_sizes = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]
bricker_selection_width = 10

#################### MAIN SCRIPT

pwbr_enabledKnobs = ['auto', 'imagewidth', 'inputChange', 'rebuild', 'connectsel', 'discon', 'pixelaspect',
                     'colcount', 'show_size', 'show_shot', 'show_channels', 'chan_filter', 'chan_filter',
                     'show_frame', 'grp', 'regexp', 'show_channel', 'timeline', 'clear_filter', 'select_bricks',
                     'font_win', 'font_mac', 'font_lin', 'extractexpr']


def getMainWindow():
    qApp = QApplication.instance()
    for widget in qApp.topLevelWidgets():
        if widget.metaObject().className() == 'Foundry::UI::DockMainWindow':
            return widget


evFilterWind = None
qNuke = getMainWindow()


def brickerGroupChanged():
    n = nuke.thisNode()
    if not n or not is_bricker(n):
        return
    knob = nuke.thisKnob()
    # if is_bricker(n):
    if not knob:
        return
    if knob.name() in pwbr_enabledKnobs:
        bricker_execute(knob)
    elif knob.name() == 'overlay':
            overlay_switch_node(n, knob.getValue())
            # elif knob.name() == 'inputChange':
            #     on = overlay_is_on()
            #     overlay_switch_node(n, not overlay_is_on())
    restore_connections(n)


class bricker_eventFilterWindowClass(QObject):
    def eventFilter(self, obj, ev):
        if ev.type() == QEvent.ChildPolished:
            self.processNode(ev.child())
        if ev.type() == QEvent.Type.ShortcutOverride:
            if ev.key() == Qt.Key_Q:
                overlay_switch_all()
        return False

    def processNode(self, n):
        nukeNode = nuke.toNode(str(n.objectName()))
        if nukeNode:
            if is_bricker(nukeNode):
                if nukeNode.Class() == pwbr_className:
                    nukeNode['error'].setVisible(False)
                    nukeNode['howto'].setVisible(False)
                bricker_addTab(nukeNode, n)
                for w in n.findChildren(QPushButton):
                    if w.text() == 'Show Help':
                        w.setStyleSheet('QPushButton{background-color:#5F3300;}')
                nukeNode.begin()
                sh = nuke.allNodes('Shuffle')
                nukeNode.end()
                if not sh:
                    QTimer.singleShot(500, lambda: nukeNode['rebuild'].execute())


def __bricker_install_old():
    d = __import__('__main__').__dict__
    if brickerExistsVar in d:
        if d[brickerExistsVar]:
            return
    global qNuke
    global evFilterWind
    d[brickerExistsVar] = 1
    evFilterWind = bricker_eventFilterWindowClass()
    qNuke.installEventFilter(evFilterWind)
    nuke.addKnobChanged(brickerGroupChanged)
    nuke.addOnCreate(brickerGroupChanged)
    # nuke.addOnScriptClose(bricker_uninstall)
    # nuke.addOnScriptLoad(bricker_install)
    overlay_menu_connect()


def bricker_install():
    d = __import__('__main__').__dict__
    if brickerExistsVar in d:
        if d[brickerExistsVar]:
            return
    global qNuke
    d[brickerExistsVar] = 1
    nuke.addKnobChanged(bricker_addtab_timer, nodeClass=pwbr_className)
    nuke.addOnCreate(brickerGroupChanged, nodeClass=pwbr_className)
    nuke.addKnobChanged(brickerGroupChanged, nodeClass=pwbr_className)
    overlay_menu_connect()


def bricker_addtab_timer():
    if nuke.thisKnob().name() == 'showPanel':
        node = nuke.thisNode()
        QTimer.singleShot(20, lambda x=node: bricker_find_node_tab_to_node(node))


def bricker_find_node_tab_to_node(nukeNode):
    # for tw in qNuke.findChildren(QTabWidget):
    #     if tw.tabText(0) == u'Bricks' and tw.count() == 4:
    #         tab = bricker_tabWidget(nukeNode, qNuke)
    #         tw.insertTab(3, tab, 'Table')
    #         tw.setCurrentIndex(0)
    if is_bricker(nukeNode):
        if nukeNode.Class() == pwbr_className:
            nukeNode['error'].setVisible(False)
            nukeNode['howto'].setVisible(False)
        bricker_addTab(nukeNode, qNuke)
        # for w in n.findChildren(QPushButton):
        #     if w.text() == 'Show Help':
        #         w.setStyleSheet('QPushButton{background-color:#5F3300;}')
        nukeNode.begin()
        sh = nuke.allNodes('Shuffle')
        nukeNode.end()
        if not sh:
            QTimer.singleShot(500, lambda: nukeNode['rebuild'].execute())

def restore_connections(node):
    pass


def save_connections(node):
    pass


def bricker_uninstall():
    global qNuke
    # global evFilterWind
    # if evFilterWind:
    #     qNuke.removeEventFilter(evFilterWind)
    nuke.removeKnobChanged(brickerGroupChanged, nodeClass=pwbr_className)
    nuke.removeOnCreate(brickerGroupChanged, nodeClass=pwbr_className)
    nuke.removeKnobChanged(bricker_addtab_timer, nodeClass='pw_bricker')

    overlay_menu_connect(0)
    d = __import__('__main__').__dict__
    if brickerExistsVar in d:
        d[brickerExistsVar] = 0


def is_bricker(node):
    if hasattr(node, 'knob'):
        return node.knob(pwbr_detectKnob) or node.Class() == pwbr_className


def bricker_addTab(node, w):
    if not w.objectName(): # is nuke window
        for tw in w.findChildren(QTabWidget):
            if tw.tabText(0) == u'Bricks' and tw.count() == 4:
                tab = bricker_tabWidget(node, qNuke)
                tw.insertTab(3, tab, 'Table')
                tw.setCurrentIndex(0)
    else:
        tabs = w.findChild(QTabWidget)
        tab = bricker_tabWidget(node, w)
        tabs.insertTab(3, tab, 'Table')
        tab.setCurrentIndex(0)

def bricker_add_tab(node, tabwidget):
    tab = bricker_tabWidget(node, qNuke)
    tabwidget.insertTab(3, tab, 'Table')


def bricker_extract_name(node, bricker):
    # if False:
        # fake import
        # from editexpr import BrickerEditRegexDialog
    data = BrickerEditRegexDialog.loads(bricker)
    if not data:
        return
    if not data['expr']:
        return
    # result, error = BrickerEditRegexDialog.evaluate_expression(
    result, error = bricker_evaluate_expression(
        data['lang'],
        data['expr'],
        node,
        data.get('group'))
    if result:
        return str(result)
    if error:
        nuke.tprint(error)
        print(error)


def bricker_evaluate_expression(lang, expr, node, regex_group=None):
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


def getShotNameFromPath(path, node):
    # node = nuke.thisNode()
    reg = node['regexp'].toScript()
    grp = node['grp'].getValue()

    shot = re.findall(reg, path)
    if shot:
        if len(shot) < int(grp) + 1:
            return '\[Group not found\]'
        return shot[int(grp)]


def getParent(node):
    return nuke.toNode('.'.join(node.fullName().split('.')[:-1])) or nuke.root()


def bricker_loadSettingKnob(node):
    if node:
        if node.knob(pwbr_prefKnob):
            val = node[pwbr_prefKnob].getValue()
            try:
                data = json.loads(val)
                return data
            except:
                node[pwbr_prefKnob].setValue("")
                return


def bricker_saveSettingKnob(node, data):
    if not node.knob(pwbr_prefKnob):
        grp1 = nuke.Tab_Knob(pwbr_prefKnobTab1, None, nuke.TABBEGINGROUP)
        i = nuke.String_Knob(pwbr_prefKnob, 'Bricker preferences')
        grp2 = nuke.Tab_Knob(pwbr_prefKnobTab2, None, nuke.TABENDGROUP)
        i.setVisible(False)
        grp1.setVisible(False)
        grp2.setVisible(False)
        node.addKnob(grp1)
        node.addKnob(i)
        node.addKnob(grp2)

    text = node[pwbr_prefKnob].getValue()
    try:
        d = json.loads(text)
    except:
        d = {}
    d.update(data)
    node[pwbr_prefKnob].setValue(json.dumps(d))


def clear_settings_from_selected(node_bricker=None):
    for i in range(node_bricker.inputs()):
        n = node_bricker.input(i)
        if n:
            if n['selected'].getValue():
                node_bricker.setInput(i, None)
                clear_node_settings(n)


def clear_node_settings(node):
    for k in [pwbr_prefKnobTab2, pwbr_prefKnob, pwbr_prefKnobTab1]:
        if node.knob(k):
            node.removeKnob(node[k])


def reset_node_settings(node):
    d = dict(mode=False,
             ofs=0,
             frm=0
             )
    bricker_saveSettingKnob(node, d)


def clear_selected_nodes(*args):
    root = nuke.thisNode() or nuke.root()
    with root:
        nodes = [n for n in nuke.selectedNodes() if not is_bricker(n)]
        for n in nodes:
            clear_node_settings(n)


def find_node(root, type):
    for n in root.dependent():
        if n.Class() == type:
            return n
        next = find_node(n, type)
        if next:
            return next


# OVERLAY
def overlay_item():
    item = [x for x in nuke.menu('Viewer').items() if x.name() == 'Overlay']
    if item:
        return item[0]


def overlay_menu_switcher(val):
    overlay_switch_all()


def overlay_menu_connect(on=True):
    item = overlay_item()
    if item:
        a = item.action()
        if on:
            if a.receivers(SIGNAL("triggered()")) == 1:
                try:
                    a.triggered[bool].connect(overlay_menu_switcher)
                except:
                    print('Not connected')
        else:
            if a.receivers(SIGNAL("triggered()")) == 2:
                try:
                    a.triggered[bool].disconnect(overlay_menu_switcher)
                except:
                    print('Not disconnected')


def overlay_is_on():
    item = overlay_item()
    if item:
        #    o.invoke()
        return item.action().isChecked()


def overlay_switch_all():
    def delayed():
        on = overlay_is_on()
        nodes = [x for x in nuke.allNodes() if is_bricker(x)]
        for n in nodes:
            n['overlay'].setValue(on)

    QTimer.singleShot(50, delayed)


def overlay_switch_node(node, on):
    if isinstance(node, str):
        node = nuke.toNode(node)
    node.begin()
    nodes = nuke.allNodes('Text') + nuke.allNodes('Text2') + nuke.allNodes('Rectangle')
    for n in nodes:
        n['disable'].setValue(not on)
        # n['disable'].setValue(on)
    node.end()


def rebuildAction():
    if not bricker_getFontPath():
        nuke.message('Error Font Path')
        return

    n = nuke.thisNode()
    n.begin()
    inputs = nuke.allNodes('Input')
    out = nuke.allNodes('Output')
    # clear
    for nod in nuke.allNodes():
        if not nod in inputs + out:
            nuke.delete(nod)
    inputs = sorted(inputs, key=lambda x: int(x.name()[5:]))
    # collect inputs
    connectedInputs = []
    for i, inp in enumerate(inputs):
        inNode = n.input(i)
        if inNode:
            connectedInputs.append([inp, inNode])
    # build setup
    computeBricks(connectedInputs)
    n.end()


def bricker_upper_copy_settings(node):
    if not node.knob(pwbr_prefKnob) and node.inputs():
        for i in range(node.inputs()):
            data = bricker_loadSettingKnob(node.input(i))
            if data:
                bricker_saveSettingKnob(node, data)


def computeBricks(inputs):
    node = nuke.thisNode()
    if not inputs:
        node[pwbr_detectKnob].setValue('Not connected')
        return
    # copy settings
    for n in inputs:
        bricker_upper_copy_settings(n[1])
    colCount, rowCount = bricker_getMatrix(len(inputs))

    width = pwbr_sizes[int(node['imagewidth'].getValue())]
    pixel = node['pixelaspect'].getValue() or 1
    colMax = max([x[1].width() for x in inputs])

    mult = float(width) / (colMax * colCount)
    imageWidth = colMax * mult
    imageHeight = max([x[1].height() * (imageWidth / x[1].width()) * (1.0 / pixel) for x in inputs])

    height = imageHeight * rowCount
    index = 0
    b = 0
    nodesToMerge = []
    timelines = []
    for j in range(rowCount):
        for i in range(colCount):
            inp, img = inputs[index]
            w = img.width()
            h = img.height() * (1.0 / pixel)
            scale = imageWidth / w
            x = imageWidth * i
            y = (height - (imageHeight * j) - imageHeight) + (imageHeight - (h * scale))

            sh = nuke.nodes.Shuffle(inputs=[inp])
            ofs = nuke.nodes.TimeOffset(inputs=[sh])
            ff = nuke.Int_Knob('finalframe', 'Final Frame')
            ofs.addKnob(ff)
            of = nuke.Int_Knob('offset', 'Offset Frame')
            ofs.addKnob(of)
            ofs['time_offset'].setExpression('-offset')
            ff.setExpression('offset + frame')
            hld = nuke.nodes.FrameHold(inputs=[sh], xpos=ofs.xpos(), ypos=ofs.ypos() + 25)
            sw = nuke.nodes.Switch(inputs=[ofs, hld], xpos=ofs.xpos(), ypos=hld.ypos() + 35, name='SW_%s' % inp.name())

            ref = nuke.nodes.Reformat(inputs=[sw], type=2, scale=scale)
            if node['select_bricks'].getValue():
                color = node['selection_color'].getValue()
                selectNode = bricker_createSelectionShape(ref, bricker_selection_width * (colCount / 2), color)
            else:
                selectNode = ref
            trScale = nuke.nodes.Transform(inputs=[selectNode])
            trScale['scale'].setValue(1.0 / pixel, 1)
            out, frameNode = bricker_createTextNode(img, trScale, ofs, hld, sw, sh, bool(node['overlay'].getValue()))
            # timeline
            if node['timeline'].getValue() and not img.firstFrame() == img.lastFrame() and img.channels():
                out, moveTl = bricker_createTimeLine(out, ref, node, frameNode)
                timelines.append(moveTl)
            tr = nuke.nodes.Transform(inputs=[out])

            tr['translate'].setValue(x, 0)
            tr['translate'].setValue(y, 1)

            nodesToMerge.append(tr)

            settings = bricker_loadSettingKnob(img)
            if settings:
                sh['in'].setValue(settings.get('layer', 'rgb'))
                ofs['offset'].setValue(settings.get('ofs', 0))
                hld['first_frame'].setValue(settings.get('frm', 0))
                sw['which'].setValue(int(settings.get('mode', 0)))

            index += 1
            if index > len(inputs) - 1:
                b = 1
                break

        if b: break
    if timelines:
        heightArray = [x['imageheight'].getValue() for x in timelines]
        maxH = max(heightArray)
        for t in timelines:
            t['translate'].setValue(-(maxH - t['imageheight'].getValue()), 1)

    mainRef = nuke.nodes.Reformat(type=1, box_fixed=True, box_width=width, box_height=height)
    nodesToMerge.insert(1, None)
    mrg = nuke.nodes.Merge2(inputs=[mainRef] + nodesToMerge)
    out = nuke.allNodes('Output')[0]
    mrg.setXYpos(out.xpos(), out.ypos() - 40)
    mainRef.setXYpos(mrg.xpos() + 150, mrg.ypos())
    out.setInput(0, mrg)
    node[pwbr_detectKnob].setValue('Input count: %s' % len(inputs))
    # QTimer.singleShot(30, lambda : overlay_switch_node(node, bool(node['overlay'].getValue())))


def bricker_getMatrix(x):
    c = int(nuke.thisNode()['colcount'].getValue())
    if not c:
        c = int(math.ceil(math.sqrt(x)))
    r = (x / c)
    if x % c:
        r += 1
    return int(c), int(r)


def bricker_getText(node):
    par = nuke.thisNode()
    if par['show_shot'].getValue():
        # path = node['file'].getValue()
        # title = getShotNameFromPath(path, nuke.thisNode())
        title = bricker_extract_name(node, par)
        if not title:
            title = '\<' + node.name() + '\>'
    else:
        title = node.name()
    info = ''

    if par['show_size'].getValue():
        info += '%s x %s' % (node.width(), node.height())

    if par['show_channels'].getValue():
        chan = node.channels()
        chan = list(set([x.split('.')[0] for x in chan]))
        fil = par['chan_filter'].getValue()
        if fil:
            chan = [z for z in map(lambda x: x if any([(y in x) for y in fil.split()]) else None, chan) if z]
        if chan:
            info += '\n' + '\n'.join(sorted(chan))
    if isinstance(title, (list, tuple)):
        title = title[0]
    return title, info.strip()


def bricker_getFontPath(node=None):
    if not node:
        node = nuke.thisNode()
    if nuke.env.get('WIN32'):
        return node['font_win'].getValue()
    elif nuke.env.get('MACOS'):
        return node['font_mac'].getValue()
    elif nuke.env.get('LINUX'):
        return node['font_lin'].getValue()

        # return nuke.thisNode()['font_current'].evaluate()


# def bricker_update_fonts(node):
#     font = bricker_getFontPath(node)
#     with node:
#         textnodes = nuke.allNodes('Text')
#         for text in textnodes:
#             text['font'].setValue(font or '')

def bricker_createTextNode(node, mrgNode, ofs, hld, sw, sh, overlay):
    title, info = bricker_getText(node)
    par = nuke.thisNode()
    pixel = par['pixelaspect'].getValue()
    alignNodes = []
    w = mrgNode.width()
    h = mrgNode.height() * (1 / pixel)
    font = bricker_getFontPath()
    text_nodes = []
    # Node name \ Shot name
    # text1 = nuke.nodes.Text2(name=nukescripts.findNextNodeName('NODENAME'))
    text1 = nuke.nodes.Text(name=nukescripts.findNextNodeName('NODENAME'))
    alignNodes.append(text1)
    text_nodes.append(text1)
    # text1['font'].setValue(font or '', 'Regilar')
    text1['font'].setValue(font or '')
    text1['yjustify'].setValue(1)
    text1['cliptype'].setValue(0)
    text1['message'].setValue(title)
    text1['box'].setExpression('.'.join([par.name(), par['fontoffset'].name()]), 0)
    expr = 'min( ({fontoffset}*max({fontMult},0.5))+(({fontsize}*{fontFactor}*max({fontMult},0.5) )), box.t) + ({fontsize}*{fontFactor}*{leading}*max({fontMult},0.5)*({lineCount}))'.format(
        fontoffset='.'.join([par.name(), par['fontoffset'].name()]),
        fontsize='.'.join([par.name(), par['fontsize'].name()]),
        fontFactor=pwbr_fontFactor,
        lineCount=len(info.split('\n')),
        # vert = '.'.join([par.name(), par['vert'].name()]),
        leading=1 + pwbr_leading,
        fontMult='.'.join([par.name(), par['imagewidth'].name()])
    )
    text1['box'].setExpression(expr, 1)
    text1['box'].setExpression('%s-%s' % (w, '.'.join([par.name(), par['fontoffset'].name()])), 2)
    text1['box'].setExpression('%s-%s' % (h, '.'.join([par.name(), par['fontoffset'].name()])), 3)
    text1['size'].setExpression(
        '{fontsize}*max({fontMult},0.5)'.format(fontsize='.'.join([par.name(), par['fontsize'].name()]),
                                                fontMult='.'.join([par.name(), par['imagewidth'].name()])))
    text1['yjustify'].setExpression('1+2*0')
    text1['xjustify'].setExpression('.'.join([par.name(), par['horiz'].name()]))
    finalFrame = nuke.Int_Knob(pwbr_currentFrameKnobName, 'Frame')
    text1.addKnob(finalFrame)
    frExpr = '[if {{[value {switch}.which]==1}} {{return [value {hold}.knob.first_frame]}} {{return  [ value {offset}.knob.finalframe  ] }}]'.format(
        switch=sw.name(),
        hold=hld.name(),
        offset=ofs.name()
    )
    finalFrame.setExpression(frExpr)
    framepatn = '.'.join([par.name(), text1.name()])
    # Image size
    text2 = nuke.nodes.Text(name=nukescripts.findNextNodeName('IMAGESIZE'))
    alignNodes.append(text2)
    text_nodes.append(text2)
    text2['font'].setValue(font)
    text2['yjustify'].setValue(1)
    text2['leading'].setValue(pwbr_leading)
    text2['cliptype'].setValue(0)
    text2['message'].setValue(info)
    text2['box'].setExpression('.'.join([par.name(), par['fontoffset'].name()]), 0)
    text2['box'].setExpression('.'.join([par.name(), par['fontoffset'].name()]), 1)
    text2['box'].setExpression('%s-%s' % (w, '.'.join([par.name(), par['fontoffset'].name()])), 2)
    text2['box'].setExpression('{height}-{offset}-({fontsize}*{width}) - ({fontsize}/2) - ({fontsize}*0.2)'.format(
        height=h,
        offset='.'.join([par.name(), par['fontoffset'].name()]),
        fontsize='.'.join([par.name(), par['fontsize'].name()]),
        width='.'.join([par.name(), par['imagewidth'].name()])), 3)
    text2['size'].setExpression(text1.name() + '.' + text1['size'].name() + "*" + str(pwbr_fontFactor))
    text2['yjustify'].setExpression('1+2*0')
    text2['xjustify'].setExpression('.'.join([par.name(), par['horiz'].name()]))

    text3 = None
    if par['show_frame'].getValue():
        # Frame
        text3 = nuke.nodes.Text(name=nukescripts.findNextNodeName('FRAME'))
        alignNodes.append(text3)
        text_nodes.append(text3)
        text3['font'].setValue(font)
        text3['yjustify'].setValue(1)
        text3['cliptype'].setValue(0)
        frExpr = '[value {text}.{knob}]'.format(text=framepatn, knob=pwbr_currentFrameKnobName)
        text3['message'].setValue('Frame: %s' % frExpr)
        text3['color'].setValue([1, 1, 1, 1])
        text3['color'].setExpression('1-{switch}.which'.format(switch='.'.join([par.name(), sw.name()])), 2)
        text3['size'].setExpression(text1.name() + '.' + text1['size'].name() + "*" + str(pwbr_fontFactor))
        text3['xjustify'].setExpression('{menu} == 2 ? 0 : 2'.format(menu='.'.join([par.name(), par['horiz'].name()])))
        text3['yjustify'].setExpression('1+2*0')
        text3['box'].setExpression('.'.join([par.name(), par['fontoffset'].name()]), 0)
        text3['box'].setExpression('.'.join([par.name(), par['fontoffset'].name()]), 1)
        text3['box'].setExpression('{h}-{offset}'.format(offset='.'.join([par.name(), par['fontoffset'].name()]), h=w),
                                   2)
        text3['box'].setExpression('{w}-{offset}'.format(offset='.'.join([par.name(), par['fontoffset'].name()]), w=h),
                                   3)
        mtext1 = nuke.nodes.Merge(inputs=[text1, text3])
        alignNodes.append(mtext1)
    else:
        mtext1 = text1

    # current channel

    text4 = None
    if par['show_channel'].getValue():
        text4 = nuke.nodes.Text(name=nukescripts.findNextNodeName('CHANNEL'))
        alignNodes.append(text4)
        text_nodes.append(text4)
        text4['font'].setValue(font)
        text4['yjustify'].setValue(3)
        text4['leading'].setValue(pwbr_leading)
        text4['cliptype'].setValue(0)
        text4['box'].setExpression('.'.join([par.name(), par['fontoffset'].name()]), 0)
        text4['box'].setExpression('.'.join([par.name(), par['fontoffset'].name()]), 1)
        text4['box'].setExpression('%s-%s' % (w, '.'.join([par.name(), par['fontoffset'].name()])), 2)
        text4['box'].setExpression('%s-%s-(%s*%s)' % (
        h, '.'.join([par.name(), par['fontoffset'].name()]), '.'.join([par.name(), par['fontsize'].name()]),
        '.'.join([par.name(), par['imagewidth'].name()])), 3)
        text4['box'].setExpression('{height}-{offset}-({fontsize}*{width}) - ({fontsize}/2)'.format(
            height=h,
            offset='.'.join([par.name(), par['fontoffset'].name()]),
            fontsize='.'.join([par.name(), par['fontsize'].name()]),
            width='.'.join([par.name(), par['imagewidth'].name()])), 3)
        text4['yjustify'].setExpression('1+2*0')
        text4['xjustify'].setExpression('{menu} == 2 ? 0 : 2'.format(menu='.'.join([par.name(), par['horiz'].name()])))
        chanexpr = '[value {parent}.{node}.knob.in]'.format(parent=par.name(), node=sh.name())
        text4['message'].setValue(chanexpr)
        text4['size'].setExpression(text1.name() + '.size' + "*" + str(pwbr_fontFactor))

        mtext1 = nuke.nodes.Merge(inputs=[text4, mtext1])
        alignNodes.append(mtext1)

    tm = nuke.nodes.Merge(inputs=[text2, mtext1])
    ed = nuke.nodes.EdgeDetectWrapper(inputs=[tm], blursize=3)
    m = nuke.nodes.Merge(inputs=[mrgNode, ed])
    # align nodes
    x, y = mrgNode.xpos(), mrgNode.ypos()
    allnodes = alignNodes + [tm, ed, m]
    for i, n in enumerate(allnodes):
        n.setXYpos(x, y + (40 * i) + 40)
    for i, n in enumerate(text_nodes):
        n['disable'].setValue(not overlay)

    return m, text1


def bricker_createTimeLine(input, img, parent, frameNode):
    w = img.width()
    # font = parent['font_current'].evaluate()
    font = bricker_getFontPath(parent)
    ref = nuke.nodes.Reformat(type=2, scale=img['scale'].getValue())
    rec1 = nuke.nodes.Rectangle(inputs=[ref])
    offsetExpr = 'max(%s,0)' % '.'.join([parent.name(), parent['tl_offset'].name()])
    heightExpr = 'max(10,%s)' % '.'.join([parent.name(), parent['tl_height'].name()])
    borderExpr = 'min(max(0,{border}), {height}/3)'.format(border='.'.join([parent.name(), parent['tl_border'].name()]),
                                                           height=heightExpr)
    currFrameExpr = '{node}.{knob}'.format(node='.'.join([parent.name(), frameNode.name()]),
                                           knob=pwbr_currentFrameKnobName)
    fontSizeExpr = frameNode.name() + '.size' + " * %s" % pwbr_fontFactor

    rec1['area'].setExpression(offsetExpr, 0)
    rec1['area'].setExpression(offsetExpr, 1)
    rec1['area'].setExpression('%s-%s' % (w, offsetExpr), 2)
    rec1['area'].setExpression('%s + %s' % (heightExpr, offsetExpr), 3)
    rec1['color'].setValue([0, 0, 0, 1])

    rec2 = nuke.nodes.Rectangle(inputs=[rec1])

    st = nuke.Int_Knob('start_frame', 'Start')
    rec2.addKnob(st)
    st.setValue(img.firstFrame())
    en = nuke.Int_Knob('end_frame', 'End')
    rec2.addKnob(en)
    en.setValue(img.lastFrame())

    rec2['area'].setExpression(rec1.name() + '.area.x+' + borderExpr, 0)
    rec2['area'].setExpression(rec1.name() + '.area.y+' + borderExpr, 1)
    maxValExpr = '{rec}.area.r-{border}'.format(rec='.'.join([parent.name(), rec1.name()]),
                                                border=borderExpr)
    exp = 'min(max(area.x,( ({frame} - start_frame) / (end_frame - start_frame) ) * ({max} - area.x) + area.x), {max})'.format(
        frame=currFrameExpr,
        max=maxValExpr)
    rec2['area'].setExpression(exp, 2)
    rec2['area'].setExpression(rec1.name() + '.area.t-' + borderExpr, 3)
    rec2['color'].setValue([0, 0, 0, 1])
    rec2['color'].setExpression('parent.timeline_color', 0)
    rec2['color'].setExpression('parent.timeline_color', 1)
    rec2['color'].setExpression('parent.timeline_color', 2)

    # frames

    fStart = nuke.nodes.Text(message='[value {val}]'.format(val='.'.join([parent.name(), rec2.name(), 'start_frame'])),
                             inputs=[rec2])
    fStart['font'].setValue(font)
    fStart['size'].setExpression(fontSizeExpr)
    fStart['yjustify'].setValue(3)
    fStart['box'].setExpression(offsetExpr, 0)
    fStart['box'].setExpression(offsetExpr + '+' + heightExpr, 1)
    fStart['box'].setExpression('%s-%s' % (w, offsetExpr), 2)
    fStart['box'].setValue(400, 3)

    fEnd = nuke.nodes.Text(message='[value {val}]'.format(val='.'.join([parent.name(), rec2.name(), 'end_frame'])),
                           inputs=[fStart])
    fEnd['font'].setValue(font)
    fEnd['size'].setExpression(fontSizeExpr)
    fEnd['yjustify'].setValue(3)
    fEnd['xjustify'].setValue(2)
    fEnd['box'].setExpression(offsetExpr, 0)
    fEnd['box'].setExpression(offsetExpr + '+' + heightExpr, 1)
    fEnd['box'].setExpression('%s-%s' % (w, offsetExpr), 2)
    fEnd['box'].setValue(400, 3)

    offsetTr = nuke.nodes.Transform(inputs=[fEnd])
    oh = nuke.Double_Knob('imageheight', 'Img Hght')
    offsetTr.addKnob(oh)
    oh.setValue(img.height())

    m = nuke.nodes.Merge(inputs=[input, offsetTr])

    x, y = input.xpos(), input.ypos()
    for i, n in enumerate([rec1, rec2, fStart, fEnd, m, ref, offsetTr]):
        n.setXYpos(x, y + (40 * i) + 40)

    return m, offsetTr


def bricker_createSelectionShape(src, width, color):
    roto = nuke.nodes.RotoPaint()
    roto.setInput(0, src)
    k = roto['curves']

    points = [[width, width],
              [width, roto.height() - width],
              [roto.width() - width, roto.height() - width],
              [roto.width() - width, width]]
    shape = rp.Shape(k)
    shape.name = 'selection_bound'
    for pt in points:
        cp = rp.ShapeControlPoint()
        cp.center.addPositionKey(0, rp.CVec2(*pt))
        shape.append(cp)
    atr = shape.getAttributes()
    atr.set(1, atr.kRedAttribute, color[0])
    atr.set(1, atr.kGreenAttribute, color[1])
    atr.set(1, atr.kBlueAttribute, color[2])
    atr.set(1, atr.kInvertedAttribute, 1)
    k.rootLayer.append(shape)
    roto['disable'].setValue(1)
    return roto


def bricker_remove_duplicates(node=None):
    node = node or nuke.thisNode()
    nodes = []
    for i in range(100):
        n = node.input(i)
        if n:
            if n in nodes:
                node.setInput(i, None)
            else:
                nodes.append(n)


# execute
def bricker_execute(knob=None, node=None):
    node = node or nuke.thisNode()
    knob = knob or nuke.thisKnob()
    if knob.name() in pwbr_enabledKnobs:
        if node['auto'].getValue() == 1.0 or knob.name() in 'rebuild':
            rebuildAction()
            if knob.name() in ['inputChange', 'rebuild']:
                d = __import__('__main__').__dict__
                if pwbr_objName in d:
                    for n in d[pwbr_objName]:
                        d[pwbr_objName][n].fillTable()
                save_connections(node)


##################### connect disconnect

def bricker_disconnect(node=None):
    node = node or nuke.thisNode()
    for i in range(node.inputs()):
        node.setInput(i, None)


def bricker_disconnect_node(node, bricker):
    for i in range(bricker.inputs()):
        if bricker.input(i) == node:
            bricker.setInput(i, None)


def bricker_connectSelected(node=None):
    node = node or nuke.thisNode()
    p = nuke.thisParent().begin()
    sel = nuke.selectedNodes()
    p.end()
    free = []
    for i in range(50):
        if not node.input(i):
            free.append(i)
    for s in sel:
        if free:
            if not s is node:
                node.setInput(free.pop(0), s)
        else:
            break


def bricker_actions_menu(node):
    actions = [
        ('Connect Selected', bricker_connectSelected),
        ('Disconnect All', bricker_disconnect),
        ('Disconnect Selected Inputs And Clear', clear_settings_from_selected),
        # ('Clear and Reset Selected Nodes', clear_selected_nodes),
        ('Remove Duplicates', bricker_remove_duplicates),
    ]

    menu = QMenu(qNuke)
    for title, act in actions:
        menu.addAction(QAction(title, qNuke, triggered=lambda a=act: a(node)))
    menu.exec_(QCursor.pos())


# widgets

class bricker_tabWidget(QWidget):
    def __init__(self, node, parent):
        super(bricker_tabWidget, self).__init__(parent)
        self.node = node
        if False:
            self.node = nuke.nodes.Node()
        self.ly = QVBoxLayout(self)
        self.setLayout(self.ly)
        self.table = QTableWidget(self)
        self.ly.addWidget(self.table)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.customMenu)
        self.table.itemDoubleClicked.connect(self.open_panel)
        self.table.itemSelectionChanged.connect(self.select_nodes)
        self.reload_btn = QPushButton('Refresh')
        self.reload_btn.clicked.connect(self.fillTable)
        self.ly.addWidget(self.reload_btn)
        self.selectionArray = {}

        d = __import__('__main__').__dict__
        if pwbr_objName in d:
            d[pwbr_objName][self.node.name()] = self
        else:
            d[pwbr_objName] = {self.node.name(): self}

        self.fillTable()
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

    def customMenu(self):
        menu = QMenu(self)

        def reset_nodes(nodes=None):
            for i in range(self.node.inputs()):
                n = self.node.input(i)
                if n in nodes:
                    self.node.setInput(i, None)
                    reset_node_settings(n)
                    self.node.setInput(i, n)
            # sel = list(set([x.row() for x in self.table.selectedIndexes()]))
            self.fillTable()
            # for i in sel:
            #     self.table.selectRow(i)

        menu.addAction(QAction('Reset', self, triggered=lambda: reset_nodes(self.selected_nodes())))

        def disconnect_selected_nodes(reset=False):
            nodes = self.selected_nodes()
            for node in nodes:
                bricker_disconnect_node(node, self.node)
            if reset:
                reset_nodes(nodes)
            self.fillTable()

        menu.addAction(QAction('Disconnect', self, triggered=disconnect_selected_nodes))
        menu.addAction(QAction('Disconnect and Reset', self, triggered=lambda: disconnect_selected_nodes(True)))
        menu.addAction(QAction('Remove Duplicates', self, triggered=lambda: bricker_remove_duplicates(self.node)))

        # def move_input(up=True):
        #     nodes = self.selected_nodes()
        #
        #     for node in nodes:
        #         print 'Move node UP', node.name(), up
        #     self.fillTable()
        # menu.addAction(QAction('Move Up', self, triggered=move_input))
        # menu.addAction(QAction('Move Down', self, triggered=lambda :move_input(False)))

        menu.exec_(QCursor.pos())

    def hideEvent(self, *args, **kwargs):
        self.clear_selection_roto()
        # main = __import__('__main__').__dict__
        # if pwbr_objName in main:
        #     if self.node.name() in main[pwbr_objName]:
        #         del main[pwbr_objName][self.node.name()]
        QWidget.hideEvent(self, *args, **kwargs)

    def showEvent(self, event):
        self.fillTable()
        QWidget.showEvent(self, event)

    def open_panel(self, item):
        i = item.row()
        d = self.table.item(i, 0).data(32)
        if d:
            d.showControlPanel()

    def selected_nodes(self, withRoto=False):
        items = self.table.selectedItems()
        nodes = []
        rows = list(set([it.row() for it in items]))
        for i in rows:
            node = self.table.item(i, 0).data(32)
            if withRoto:
                nodes.append((node, self.selectionArray.get(i)))
            else:
                nodes.append(node)
        return nodes

    def select_nodes(self, *args):
        nodes = self.selected_nodes(True)
        nukescripts.clear_selection_recursive()
        self.clear_selection_roto()
        if nodes:
            for n in nodes:
                n[0].setSelected(True)
                if n[1]:
                    n[1]['disable'].setValue(False)
                    # else:
                    #     print 'Roto not found for', n[0].name()

    def clear_selection_roto(self):
        with self.node:
            for node in nuke.allNodes('RotoPaint'):
                node['disable'].setValue(True)

    def find_selection_roto(self, i):
        with self.node:
            input = sorted(nuke.allNodes('Input'), key=lambda x: int(x.name()[5:]))[i]
            n = find_node(input, 'RotoPaint')
            return n

    def fillTable(self):
        main = __import__('__main__').__dict__
        # savedSelection = self.selected_nodes()
        # select_index = []
        try:
            self.table.clear()
        except:
            return
        if pwbr_objName in main:
            # try:
            nodes = []
            for i in range(100):
                inp = self.node.input(i)
                if inp:
                    nodes.append([inp, i])
            self.table.setColumnCount(5)
            self.table.setColumnWidth(0, 20)
            self.table.setRowCount(len(nodes))
            labels = [str(x[1] + 1) for x in nodes]
            self.table.setVerticalHeaderLabels(labels)
            self.table.setHorizontalHeaderLabels(['Node', 'Size', 'Shot', 'Frame', 'Channel'])
            extract_name = self.node['show_shot'].getValue()
            for i, nd in enumerate(nodes):
                col = 0
                currentNode, inp = nd
                # if currentNode in savedSelection:
                #     select_index.append(i)
                roto = self.find_selection_roto(inp)
                self.selectionArray[i] = roto
                # node name
                item = QTableWidgetItem(currentNode.name())
                self.table.setItem(i, col, item)
                item.setData(32, currentNode)
                # image size
                col += 1
                sz = '%s x %s' % (currentNode.width(), currentNode.height())
                item = QTableWidgetItem(sz)
                self.table.setItem(i, col, item)
                # shot name
                col += 1
                item = QTableWidgetItem()
                if extract_name:
                    title = bricker_extract_name(currentNode, self.node)
                    item.setText(title or '')
                # if currentNode.Class() == 'Write':
                #     path = currentNode['file'].getValue()
                #     title = getShotNameFromPath(path, self.node)
                #     if title:
                #         item.setText(title)
                self.table.setItem(i, col, item)
                # frame
                col += 1
                fr = bricker_setFrameWidgetClass(currentNode, inp, self.node, self)
                self.table.setCellWidget(i, col, fr)

                # layer
                col += 1
                ch = self.getChannels(currentNode)
                d = bricker_loadSettingKnob(currentNode)
                box = bricker_layerListClass(currentNode, inp, self.node, ch, d, self)

                self.table.setCellWidget(i, col, box)
                # move buttons
                # restore selection
                # self.table.blockSignals(1)
                # for i in select_index:
                #     print i
                #     self.table.selectRow(i)
                # self.table.blockSignals(0)

        else:
            print('ERROR REBUILD TABLE')

    def getChannels(self, node):
        chan = node.channels()
        names = [x.split('.')[0] for x in chan]
        res = []
        for ch in names:
            if not ch in res:
                res.append(ch)
        # create shuffle
        return res


class bricker_setFrameWidgetClass(QWidget):
    tooltipText = 'Press Ctrl when switch to HLD to keep current frame frozen'
    use_slider = True

    def __init__(self, node, inp, mainNode, table):
        super(bricker_setFrameWidgetClass, self).__init__()
        self.node = node
        self.inp = inp
        self.main = mainNode
        self.table = table
        self.ly = QHBoxLayout(self)
        self.ly.setContentsMargins(0, 0, 0, 0)
        self.ly.setSpacing(0)

        self.ofs = self.hld = self.sw = self.sfl = None

        self.switcher = QPushButton(pwbr_setFrameLabel)
        self.switcher.setFlat(1)
        self.switcher.setCheckable(1)
        self.switcher.clicked.connect(self.switchMode)
        self.switcher.setMinimumWidth(40)
        self.switcher.setMaximumWidth(40)
        self.ly.addWidget(self.switcher)
        self.switcher.setToolTip(self.tooltipText)
        self.switcher.setStyleSheet("QToolTip { color: #000; background-color: #ffffdc; border: 1px solid black; }")
        # self.holdFrame = QSpinBox()
        # self.holdFrame.setButtonSymbols(QAbstractSpinBox.NoButtons)
        # self.holdFrame.setMinimumHeight(20)
        # self.holdFrame.setMinimum(-999999)
        # self.holdFrame.setMaximum(999999)
        # self.holdFrame.setStyleSheet('border:none;text-align: center;')
        self.holdFrame = self.frame_widget('hld')

        self.holdFrame.valueChanged.connect(self.changeValue)
        self.ly.addWidget(self.holdFrame)

        self.offsetFrame = self.frame_widget('ofs')
        # self.offsetFrame = QSpinBox()
        # self.offsetFrame.setButtonSymbols(QAbstractSpinBox.NoButtons)
        # self.offsetFrame.setMinimumHeight(20)
        # self.offsetFrame.setMinimum(-999999)
        # self.offsetFrame.setMaximum(999999)
        # self.offsetFrame.setStyleSheet('border:none;text-align: center;')
        self.offsetFrame.valueChanged.connect(self.changeValue)
        self.ly.addWidget(self.offsetFrame)

        self.ofs, self.hld, self.sw = self.getNodes()

        self.switchMode()

        self.initUI()

    def frame_widget(self, type):
        if not self.use_slider:
            wd = QSpinBox()
            wd.setButtonSymbols(QAbstractSpinBox.NoButtons)
            wd.setMinimumHeight(20)
            wd.setMinimum(-999999)
            wd.setMaximum(999999)
            wd.setStyleSheet('border:none;text-align: center;')
            return wd
        else:
            wd = bricker_FrameWidget(type, self.node)
            return wd

    def initUI(self):
        d = self.loadSettingKnob()
        if d:
            self.switcher.setChecked(d.get('mode', False))
            self.holdFrame.setValue(d.get('frm', 0))
            self.offsetFrame.setValue(d.get('ofs', 0))
            self.updateNode()

    def switchMode(self):
        if not self.hld or not self.ofs:
            return
        if not self.switcher.isChecked():
            self.switcher.setText(pwbr_offsetFrameLabel)
            self.holdFrame.setVisible(0)
            self.offsetFrame.setVisible(1)

            self.offsetFrame.setValue(self.ofs['offset'].getValue())
        else:
            if QApplication.keyboardModifiers() == Qt.ControlModifier:
                frame = self.get_current_frame()
                if not frame is None:
                    self.holdFrame.setValue(frame)
            self.switcher.setText(pwbr_setFrameLabel)
            self.holdFrame.setVisible(self.hld['first_frame'].getValue())
            self.offsetFrame.setVisible(0)
            self.holdFrame.setVisible(1)
        self.updateNode()

    def get_current_frame(self):
        self.main.begin()
        i = nuke.allNodes('Input')[self.inp]
        node = None
        for x in i.dependent()[0].dependent():
            if x.Class() == 'TimeOffset':
                node = x
                break
        self.main.end()
        k = node.knob('finalframe')
        if k:
            return k.getValue()

    def changeValue(self, i):
        self.updateNode()

    def getNodes(self):
        self.main.begin()
        inputs = nuke.allNodes('Input')
        inputs = sorted(inputs, key=lambda x: int(x.name()[5:]))
        i = inputs[self.inp]
        ofs = find_node(i, 'TimeOffset')
        hld = find_node(i, 'FrameHold')
        sw = None
        if ofs:
            sw = [x for x in ofs.dependent() if x.Class() == 'Switch']
            if sw:
                sw = sw[0]
        self.main.end()
        if ofs:
            self.offsetFrame.setValue(ofs['offset'].getValue())
        if hld:
            self.holdFrame.setValue(hld['first_frame'].getValue())
        if sw:
            if sw['which'].getValue() == 0:  # offset
                self.switcher.setText(pwbr_offsetFrameLabel)
                self.switcher.setChecked(0)
                self.holdFrame.setVisible(0)
                self.offsetFrame.setVisible(1)
            else:  # hold
                self.switcher.setText(pwbr_setFrameLabel)
                self.switcher.setChecked(1)
                self.holdFrame.setVisible(1)
                self.offsetFrame.setVisible(0)
        return ofs, hld, sw

    def updateNode(self):
        if self.ofs:
            self.ofs['offset'].setValue(self.offsetFrame.value())
        if self.hld:
            self.hld['first_frame'].setValue(self.holdFrame.value())
        if self.sw:
            self.sw['which'].setValue(int(self.switcher.isChecked()))
        self.saveSettingKnob()

    def loadSettingKnob(self):
        return bricker_loadSettingKnob(self.node)

    def saveSettingKnob(self):
        d = dict(mode=self.switcher.isChecked(),
                 ofs=self.offsetFrame.value(),
                 frm=self.holdFrame.value()
                 )
        bricker_saveSettingKnob(self.node, d)


class bricker_FrameSlider(QSlider):
    handle_width = 10
    slider_style = '''
    QSlider::groove:horizontal {
        border: 1px solid #000;
        background: #000;
        height: 3px;
        border-radius: 0px;
    }
    QSlider::sub-page:horizontal {
        background:  #404040;
        border: 1px solid #000;
        height: 10px;
        border-radius: 0px;
    }
    QSlider::add-page:horizontal {
        background: #404040;
        border: 1px solid #000;
        height: 10px;
        border-radius: 0px;
    }
        QSlider::handle:horizontal {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,   stop:0 #696969, stop:1 #505050);
        border: 1px solid #000;
        width: %spx;
        margin-top: -8px;
        margin-bottom: -8px;
        border-radius: 0px;
    }
        QSlider::hover
    {
        background: #3f3f3f;
    }
    ''' % handle_width

    def __init__(self, type, node, *args, **kwargs):
        super(bricker_FrameSlider, self).__init__(*args, **kwargs)
        self.setMinimumHeight(25)
        self.setMinimumWidth(100)
        self.setSingleStep(1)
        self.setPageStep(1)
        # self.setStyleSheet(self.slider_style)
        self._min = -100
        self._max = 100
        self._set_max = None
        self._set_min = None
        if type == 'ofs':
            self.valueChanged.connect(self.soft_range)
        else:
            if isinstance(node, list):
                self._min = node[0]
                self._max = node[1]
            else:
                if isinstance(node, list):
                    self._min = node[0]
                    self._max = node[1]
                else:
                    self._min = node.firstFrame()
                    self._max = node.lastFrame()

        self.setMinimum(self._min)
        self.setMaximum(self._max)

    def soft_range(self, v):
        sz = max(int(abs(self._max - self._min) * 0.1), 3)
        if v < self._min + sz:
            self._min = self._min - (abs(self._max - self._min)/2)
            self._set_min = self._min
        if v > self._max - sz:
            self._max = self._max + (abs(self._max - self._min)/2)
            self._set_max = self._max

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # handle_pos = self.setRange(self.value(), self.minimum(), self.maximum(), 0, self.width())
            # click_x = event.x()
            # if not (click_x < handle_pos-(self.handle_width/2) and click_x > handle_pos+(self.handle_width/2)):
            #     print 'move'
            self.setValue(self.minimum() + ((self.maximum() - self.minimum()) * event.x()) / self.width() )
        super(bricker_FrameSlider, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setValue(self.minimum() + ((self.maximum() - self.minimum()) * event.x()) / self.width())
        super(bricker_FrameSlider, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._set_min:
            self.setMinimum(self._set_min)
            self._set_min = None
        if self._set_max:
            self.setMaximum(self._set_max)
            self._set_max = None

        super(bricker_FrameSlider, self).mouseReleaseEvent(event)

    def setValue(self, v):
        if v < self.minimum():
            self.setMinimum(v - 50)
        if v > self.maximum():
            self.setMaximum(v + 50)
        super(bricker_FrameSlider, self).setValue(v)

    @staticmethod
    def setRange(x=0.0, oldmin=0.0, oldmax=1.0, newmin=0.0, newmax=1.0):
        if oldmin < oldmax:
            realoldmin = oldmin
            realoldmax = oldmax
            realnewmin = newmin
            realnewmax = newmax
        elif oldmin > oldmax:
            realoldmin = oldmax
            realoldmax = oldmin
            realnewmin = newmax
            realnewmax = newmin
        else:
            return x
        if x < realoldmin:
            result = realnewmin
        elif x > realoldmax:
            result = realnewmax
        else:
            result = (realnewmin + (realnewmax - realnewmin) * (x - oldmin) / (oldmax - oldmin))
        return result


class bricker_FrameWidget(QWidget):
    valueChanged = Signal(int)

    def __init__(self, type, node, *args, **kwargs):
        super(bricker_FrameWidget, self).__init__(*args, **kwargs)
        self.setWindowFlags(Qt.Window)
        self.setMinimumHeight(20)
        self.setMinimumWidth(100)
        self.ly = QHBoxLayout()
        self.setLayout(self.ly)
        self.setContentsMargins(0, 0, 0, 0)
        self.sld = bricker_FrameSlider(type, node, Qt.Horizontal)
        self.sld.setSingleStep(1)
        self.sld.setPageStep(1)
        self.sld.valueChanged.connect(self.value_changed)

        self.spb = QSpinBox()
        self.spb.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.spb.setMinimumHeight(20)
        self.spb.setMinimum(-999999)
        self.spb.setMaximum(999999)
        self.spb.valueChanged.connect(self.value_changed)

        self.setLayout(self.ly)
        self.ly.addWidget(self.sld)
        self.ly.addWidget(self.spb)

    def value_changed(self, v):
        if self.sender() == self.sld:
            self.spb.blockSignals(1)
            self.spb.setValue(v)
            self.spb.blockSignals(0)
        elif self.sender() == self.spb:
            self.sld.blockSignals(1)
            self.sld.setValue(v)
            self.sld.blockSignals(0)
        self.valueChanged.emit(v)

    def setValue(self, v):
        self.spb.blockSignals(1)
        self.spb.setValue(v)
        self.spb.blockSignals(0)
        self.sld.blockSignals(1)
        self.sld.setValue(v)
        self.sld.blockSignals(0)

    def value(self):
        return self.sld.value()


class bricker_layerListClass(QComboBox):
    def __init__(self, node, inp, mainNode, channels, saved, parent):
        super(bricker_layerListClass, self).__init__(parent)
        self.main = mainNode
        self.imgNode = self.main.input(inp)
        self.node = node
        if channels:
            self.addItems(channels)
        else:
            self.setEnabled(0)
        self.sfl = self.get_node(mainNode, inp)
        if self.sfl:
            layer = self.sfl['in'].value()
            index = self.findText(layer)
            if index > 0:
                self.setCurrentIndex(index)
        self.currentIndexChanged.connect(self.set_layer)

    def set_layer(self):
        self.sfl['in'].setValue(self.currentText())
        bricker_saveSettingKnob(self.imgNode, {'layer': self.currentText()})

    def get_node(self, main, inp):
        main.begin()
        inputs = nuke.allNodes('Input')
        inputs = sorted(inputs, key=lambda x: int(x.name()[5:]))
        i = inputs[inp]
        main.end()
        return find_node(i, 'Shuffle')

def getMainWindow():
    qApp = QApplication.instance()
    for widget in qApp.topLevelWidgets():
        if widget.metaObject().className() == 'Foundry::UI::DockMainWindow':
            return widget

if __name__ == '__main__':
    # gizmo mode
    bricker_install()
else:
    # test mode
    __import__('__main__').__dict__['bricker_actions_menu'] = bricker_actions_menu


#################### load other knobs ######

exec(nuke.thisNode().knob('editexprwindow').value())

#################### FIX CALLBACK ERRORS

from nuke import callbacks


def _doCallbacks(dict, node=None):
    list = dict.get(nuke.thisClass())
    node = nuke.thisNode()
    if list:
        for f in list:
            if f[3] == None or f[3] is node:
                f[0](*f[1], **f[2])
    list = dict.get('*')
    if list:
        try:
            for f in list:
                if f[3] == None or f[3] is node:
                    f[0](*f[1], **f[2])
        except:
            pass


callbacks._doCallbacks = _doCallbacks

