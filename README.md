# NUKE BRICKER

Nuke Gizmo for supervising shots.

# Usage
### [Video Tutorial](https://youtu.be/z18xjO2nJfg)

### [Tricks](https://youtu.be/TFQaIXKqf1Q)

# Install

1. Copy this code to __menu.py__

```python
import nuke

toolbar = nuke.toolbar("Nodes")
toolbar.addCommand( "Merge/Bricker", "nuke.createNode(\"pw_bricker\")", icon="bricker.png")
def install_bricker():
    nuke.thisNode()['mainScript'].execute()
    nuke.removeOnCreate(install_bricker, nodeClass='pw_bricker')
nuke.addOnCreate(install_bricker, nodeClass='pw_bricker')

#fix overlay action
nuke.menu('Viewer').items()[1].action().setChecked(True)
```

2. Copy __bricker.png__ to NUKE_PATH

3. Restart Nuke


# Save from source

If you have an older or newer version you can save gizmo for your version youself.

1. Open terminal or cmd shell

2. Go to repository root

```bash
cd .../nuke_bricker
```

3. Start Nukes python with script *compile_nk.py*

```bash
/path/to/your/Nuke##.#v#/python compile_nk.py
```

Now new script is created from sources and saved to .../nuke_bricker/dist

4. Open script .../nuke_bricker/dist/bricker_gizmo.nk in Nuke

5. Open Control Panel of bricker node, go to tab *Node* and press __export as gizmo...__.
Select path to some NUKE_PATH location and press *Save*.

New version of gizmo is saved!


1. Open file */src/bricker_source.nk* in Nuke

2. Open **Control Panel** of group *bricker*

3. Go to tab **Node**

4. Press button **export as gizmo...**

5. Select old gizmo location and overwrite file.
**Attention! Don't change gizmo name! It should be named "pw_bricker.gizmo". This is important!**


# known issues

1. Break connection when copy\paste