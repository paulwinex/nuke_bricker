import nuke

toolbar = nuke.toolbar("Nodes")
toolbar.addCommand( "Merge/Bricker", "nuke.createNode(\"pw_bricker\")", icon="bricker.png")


def install_bricker():
    nuke.thisNode()['mainScript'].execute()
    nuke.removeOnCreate(install_bricker, nodeClass='pw_bricker')


nuke.addOnCreate(install_bricker, nodeClass='pw_bricker')


# fix overlay action
nuke.menu('Viewer').items()[1].action().setChecked(True)
