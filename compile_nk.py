import os, glob
import nuke

root = os.getcwd()
src_dir = os.path.join(root, 'src')
src_script = os.path.join(src_dir, 'bricker_source.nk')
dst_dir = os.path.join(root, 'dist')
dst_script = os.path.join(dst_dir, 'bricker_gizmo.nk')
if not os.path.exists(src_script):
    raise IOError('Source script not found. Please start this script from repository root')

knob_scripts = glob.glob(src_dir+'/*.py')
nuke.scriptClear()
nuke.scriptOpen(src_script)
node = nuke.toNode('bricker')
for script in knob_scripts:
    knob = os.path.splitext(os.path.basename(script))[0]
    if knob.startswith('_'):
        continue
    node[knob].setValue(open(script).read())

if not os.path.exists(dst_dir):
    os.makedirs(dst_dir)
if os.path.exists(dst_script):
    os.remove(dst_script)
nuke.scriptSaveAs(dst_script)
print('Updated bricker script saved to: {}'.format(dst_script))
print ('Now open the script in your Nuke and export the gizmo!')
