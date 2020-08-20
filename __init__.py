# import the main window object (mw) from aqt
from aqt import mw
# import all of the Qt GUI library
from aqt.qt import *
# import the deck manager API
from anki.decks import DeckManager
from anki.utils import intTime

# import the anki apkg importers
from anki.importing.apkg import AnkiPackageImporter
import os

class CustomImporter(AnkiPackageImporter):
	def _did(self, did: int):
		"Given did in src col, return local id."
		# already converted?
		if did in self._decks:
			return self._decks[did]
		# get the name in src
		g = self.src.decks.get(did)
		name = g["name"]
		# if there's a prefix, replace the top level deck
		if self.deckPrefix:
			tmpname = "::".join(DeckManager.path(name)[1:])
			name = self.deckPrefix
			if tmpname:
				name += "::" + tmpname

		# if target is a filtered deck, we'll need a new deck name
		deck = self.dst.decks.byName(name)
		if deck and deck["dyn"]:
			name = "%s %d" % (name, intTime())
		# create in local
		newid = self.dst.decks.id(name)
		# pull conf over
		if "conf" in g and g["conf"] != 1:
			conf = self.src.decks.get_config(g["conf"])
			self.dst.decks.save(conf)
			self.dst.decks.update_config(conf)
			g2 = self.dst.decks.get(newid)
			g2["conf"] = g["conf"]
			self.dst.decks.save(g2)
		# save desc
		deck = self.dst.decks.get(newid)
		deck["desc"] = g["desc"]
		self.dst.decks.save(deck)
		# add to deck map and return
		self._decks[did] = newid
		return newid

# We're going to add a menu item below. First we want to create a function to
# be called when the menu item is activated.
def importFromFolder():
	mw.importDialog = QFileDialog()
	mw.importDialog.setFileMode(QFileDialog.Directory)

	if mw.importDialog.exec_():
		fileNames = mw.importDialog.selectedFiles()

		if len(fileNames) > 0:
			rootDir = fileNames[0]
			baseName = os.path.basename(rootDir)
			prefixLen = len(rootDir) - len(baseName)
			for root, subDirs, files in os.walk(rootDir):
				for f in files:
					if f.endswith(".apkg"):
						# Get name for deck
						deckName = "::".join(root[prefixLen:].split(os.sep)) + "::" + f[0: len(f) - 5]

						did = mw.col.decks.id(deckName)
						mw.col.decks.save(mw.col.decks.get(did))
						importer = CustomImporter(mw.col, os.path.join(root, f))
						importer.deckPrefix = deckName
						importer.run()

			mw.reset()

# create a new menu item
action = QAction("Import From Folder", mw)
# set it to call importFromFolder when it's clicked
action.triggered.connect(importFromFolder)
# and add it to the tools menu
mw.form.menuTools.addAction(action)
