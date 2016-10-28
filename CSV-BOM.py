#Author-Peter Boeker
#Description-Provides customizable prefixes to collect browser components with there boundary box dimention or volume.

import adsk.core
import adsk.fusion
import adsk.cam
import traceback
import json

# Global list to keep all event handlers in scope.
# This is only needed with Python.
handlers = []

app = adsk.core.Application.get()
ui = app.userInterface
cmdId = "CSVBomAddInMenuEntry"
cmdName = "CSV-BOM"
dialogTitle = "Create BOM"
cmdDesc = "Creates a bill of material from the browser components."
cmdRes = ".//ressources//CSV-BOM"

# Event handler for the commandCreated event.
class BOMCommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
	global cmdId
	global ui
	def __init__(self):
		super().__init__()
	def notify(self, args):
		product = app.activeProduct
		design = adsk.fusion.Design.cast(product)
		lastPrefs = design.attributes.itemByName(cmdId, "lastUsedOptions")
		_onlySelectedComps = False
		_includeBoundingboxDims = True
		_ignoreUnderscorePrefixedComps = True
		_underscorePrefixStrip = False
		_ignoreCompsWithoutBodies = True
		_ignoreLinkedComps = True
		_ignoreVisibleState = True
		_includeVolume = False
		_includeArea = False
		_includeMass = False
		_includeDensity = False
		_includeMaterial = False
		if lastPrefs:
			try:
				lastPrefs = json.loads(lastPrefs.value)
				_onlySelectedComps = lastPrefs["onlySelComp"]
				_includeBoundingboxDims = lastPrefs["incBoundDims"]
				_ignoreUnderscorePrefixedComps = lastPrefs["ignoreUnderscorePrefComp"]
				_underscorePrefixStrip = lastPrefs["underscorePrefixStrip"]
				_ignoreCompsWithoutBodies = lastPrefs["ignoreCompWoBodies"]
				_ignoreLinkedComps = lastPrefs["ignoreLinkedComp"]
				_ignoreVisibleState = lastPrefs["ignoreVisibleState"]
				_includeVolume = lastPrefs["incVol"]
				_includeArea = lastPrefs["incArea"]
				_includeMass = lastPrefs["incMass"]
				_includeDensity = lastPrefs["incDensity"]
				_includeMaterial = lastPrefs["incMaterial"]
			except:
				ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
				return

		eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
		cmd = eventArgs.command
		inputs = cmd.commandInputs
		ipSelectComps = inputs.addBoolValueInput(cmdId + "_onlySelectedComps", "Selected only", True, "", _onlySelectedComps)
		ipSelectComps.tooltip = "Only selected components will be used"

		ipBoundingBox = inputs.addBoolValueInput(cmdId + "_includeBoundingboxDims", "Include dimension", True, "", _includeBoundingboxDims)
		ipBoundingBox.tooltip = "Will include the bounding box dimensions of all bodies related the parent component."

		ipUnderscorePrefix = inputs.addBoolValueInput(cmdId + "_ignoreUnderscorePrefixedComps", 'Exclude "_"', True, "", _ignoreUnderscorePrefixedComps)
		ipUnderscorePrefix.tooltip = 'Exclude all components there name starts with "_"'

		ipUnderscorePrefixStrip = inputs.addBoolValueInput(cmdId + "_underscorePrefixStrip", 'Strip "_"', True, "", _underscorePrefixStrip)
		ipUnderscorePrefixStrip.tooltip = 'If checked, "_" is stripped from components name'
		if _ignoreUnderscorePrefixedComps is True:
			ipUnderscorePrefixStrip.isVisible = False
		else:
			ipUnderscorePrefixStrip.isVisible = True

		ipWoBodies = inputs.addBoolValueInput(cmdId + "_ignoreCompsWithoutBodies", "Exclude if no bodies", True, "", _ignoreCompsWithoutBodies)
		ipWoBodies.tooltip = "Exclude all components if they have at least one body"

		ipLinkedComps = inputs.addBoolValueInput(cmdId + "_ignoreLinkedComps", "Exclude linked", True, "", _ignoreLinkedComps)
		ipLinkedComps.tooltip = "Exclude all components they are linked into the design"

		ipVisibleState = inputs.addBoolValueInput(cmdId + "_ignoreVisibleState", "Ignore visible state", True, "", _ignoreVisibleState)
		ipVisibleState.tooltip = "Ignores the visible state for components"

		grpPhysics = inputs.addGroupCommandInput(cmdId + "_grpPhysics", "Additional Physics")
		if _includeVolume is True or _includeArea is True or _includeMass is True or _includeDensity is True or _includeMaterial is True:
			grpPhysics.isExpanded = True
		else:
			grpPhysics.isExpanded = False
		grpPhysicsChildren = grpPhysics.children

		ipVolume = grpPhysicsChildren.addBoolValueInput(cmdId + "_includeVolume", "Include volume", True, "", _includeVolume)
		ipVolume.tooltip = "Adds the calculated volume of all bodies related to the parent component"

		ipIncludeArea = grpPhysicsChildren.addBoolValueInput(cmdId + "_includeArea", "Include area", True, "", _includeArea)
		ipIncludeArea.tooltip = "Include component area in cm^2"

		ipIncludeMass = grpPhysicsChildren.addBoolValueInput(cmdId + "_includeMass", "Include mass", True, "", _includeMass)
		ipIncludeMass.tooltip = "Include component mass in kg"

		ipIncludeDensity = grpPhysicsChildren.addBoolValueInput(cmdId + "_includeDensity", "Include density", True, "", _includeDensity)
		ipIncludeDensity.tooltip = "Include component density in kg/cm^3"

		ipIncludeMaterial = grpPhysicsChildren.addBoolValueInput(cmdId + "_includeMaterial", "Include material", True, "", _includeMaterial)
		ipIncludeMaterial.tooltip = "Include component physical material"

		# Connect to the execute event.
		onExecute = BOMCommandExecuteHandler()
		cmd.execute.add(onExecute)
		handlers.append(onExecute)

		onInputChanged = BOMCommandInputChangedHandler()
		cmd.inputChanged.add(onInputChanged)
		handlers.append(onInputChanged)


# Event handler for the execute event.
class BOMCommandExecuteHandler(adsk.core.CommandEventHandler):
	global cmdId
	def __init__(self):
		super().__init__()
	def collectData(self, design, bom, prefs):
		csvStr = ''
		defaultUnit = design.fusionUnitsManager.defaultLengthUnits
		csvHeader = ["Part name", "Amount"]
		if prefs["incVol"]:
			csvHeader.insert(len(csvHeader), "Volume")
		if prefs["incBoundDims"]:
			csvHeader.insert(len(csvHeader), "Dimension " + defaultUnit)
		if prefs["incArea"]:
			csvHeader.insert(len(csvHeader), "Area cm^2")
		if prefs["incMass"]:
			csvHeader.insert(len(csvHeader), "Mass kg")
		if prefs["incDensity"]:
			csvHeader.insert(len(csvHeader), "Density kg/cm^2")
		if prefs["incMaterial"]:
			csvHeader.insert(len(csvHeader), "Material")
		for k in csvHeader:
			csvStr += k + ';'
		csvStr += '\n'
		for item in bom:
			dims = ''
			name = item["name"]
			if prefs["ignoreUnderscorePrefComp"] is False and prefs["underscorePrefixStrip"] is True and name[0] == '_':
				name = name[1:]
			csvStr += '"' + name + '";' + str(item["instances"]) + ';'
			if prefs["incVol"]:
				csvStr += str(item["volume"]) + ';'
			if prefs["incBoundDims"]:
				dim = 0
				for k in item["boundingBox"]:
					dim += item["boundingBox"][k]
				if dim > 0:
					bbX = "{0:.3f}".format(float(design.fusionUnitsManager.formatInternalValue(item["boundingBox"]["x"], defaultUnit, False)))
					bbY = "{0:.3f}".format(float(design.fusionUnitsManager.formatInternalValue(item["boundingBox"]["y"], defaultUnit, False)))
					bbZ = "{0:.3f}".format(float(design.fusionUnitsManager.formatInternalValue(item["boundingBox"]["z"], defaultUnit, False)))
					dims += str(bbX) + ' x '
					dims += str(bbY) + ' x '
					dims += str(bbZ)
				csvStr += dims + ';'
			if prefs["incArea"]:
				csvStr += str("{0:.2f}".format(item["area"])) + ';'
			if prefs["incMass"]:
				csvStr += str("{0:.5f}".format(item["mass"])) + ';'
			if prefs["incDensity"]:
				csvStr += str("{0:.5f}".format(item["density"])) + ';'
			if prefs["incMaterial"]:
				csvStr += item["material"] + ';'
			csvStr += '\n'
		return csvStr

	def getPrefsObject(self, inputs):
		obj = {
			"onlySelComp": inputs.itemById(cmdId + "_onlySelectedComps").value,
			"incBoundDims": inputs.itemById(cmdId + "_includeBoundingboxDims").value,
			"ignoreUnderscorePrefComp": inputs.itemById(cmdId + "_ignoreUnderscorePrefixedComps").value,
			"underscorePrefixStrip": inputs.itemById(cmdId + "_underscorePrefixStrip").value,
			"ignoreCompWoBodies": inputs.itemById(cmdId + "_ignoreCompsWithoutBodies").value,
			"ignoreLinkedComp": inputs.itemById(cmdId + "_ignoreLinkedComps").value,
			"ignoreVisibleState": inputs.itemById(cmdId + "_ignoreVisibleState").value,
			"incVol": inputs.itemById(cmdId + "_includeVolume").value,
			"incArea": inputs.itemById(cmdId + "_includeArea").value,
			"incMass": inputs.itemById(cmdId + "_includeMass").value,
			"incDensity": inputs.itemById(cmdId + "_includeDensity").value,
			"incMaterial": inputs.itemById(cmdId + "_includeMaterial").value
		}
		return obj

	def getBodiesVolume(self, bodies):
		volume = 0
		for bodyK in bodies:
			if bodyK.isSolid:
				volume += bodyK.volume
		return volume

	def getBodiesBoundingBox(self, bodies):
		minPointX = maxPointX = minPointY = maxPointY = minPointZ = maxPointZ = 0
		# Examining the maximum min point distance and the maximum max point distance.
		for body in bodies:
			if body.isSolid:
				if not minPointX or body.boundingBox.minPoint.x < minPointX:
					minPointX = body.boundingBox.minPoint.x
				if not maxPointX or body.boundingBox.maxPoint.x > maxPointX:
					maxPointX = body.boundingBox.maxPoint.x
				if not minPointY or body.boundingBox.minPoint.y < minPointY:
					minPointY = body.boundingBox.minPoint.y
				if not maxPointY or body.boundingBox.maxPoint.y > maxPointY:
					maxPointY = body.boundingBox.maxPoint.y
				if not minPointZ or body.boundingBox.minPoint.z < minPointZ:
					minPointZ = body.boundingBox.minPoint.z
				if not maxPointZ or body.boundingBox.maxPoint.z > maxPointZ:
					maxPointZ = body.boundingBox.maxPoint.z
		return {
			"x": maxPointX - minPointX,
			"y": maxPointY - minPointY,
			"z": maxPointZ - minPointZ
		}

	def getPhysicsArea(self, bodies):
		area = 0
		for body in bodies:
			if body.isSolid:
				if body.physicalProperties:
					area += body.physicalProperties.area
		return area

	def getPhysicalMass(self, bodies):
		mass = 0
		for body in bodies:
			if body.isSolid:
				if body.physicalProperties:
					mass += body.physicalProperties.mass
		return mass

	def getPhysicalDensity(self, bodies):
		density = 0
		if bodies.count > 0:
			body = bodies.item(0)
			if body.isSolid:
				if body.physicalProperties:
					density = body.physicalProperties.density
			return density

	def getPhysicalMaterial(self, bodies):
		matList = []
		for body in bodies:
			if body.isSolid and body.material:
				mat = body.material.name
				if mat not in matList:
					matList.append(mat)
		return ', '.join(matList)

	def notify(self, args):
		global app
		global ui
		global dialogTitle
		global cmdId

		product = app.activeProduct
		design = adsk.fusion.Design.cast(product)
		eventArgs = adsk.core.CommandEventArgs.cast(args)
		inputs = eventArgs.command.commandInputs

		if not design:
			ui.messageBox('No active design', dialogTitle)
			return

		try:
			prefs = self.getPrefsObject(inputs)

			# Get all occurrences in the root component of the active design
			root = design.rootComponent
			occs = []
			if prefs["onlySelComp"]:
				if ui.activeSelections.count > 0:
					selections = ui.activeSelections
					for selection in selections:
						if (hasattr(selection.entity, "objectType") and selection.entity.objectType == adsk.fusion.Occurrence.classType()):
							occs.append(selection.entity)
							if selection.entity.component:
								for item in selection.entity.component.allOccurrences:
									occs.append(item)
						else:
							ui.messageBox('No components selected!\nPlease select some components.')
							return
				else:
					ui.messageBox('No components selected!\nPlease select some components.')
					return
			else:
				occs = root.allOccurrences

			if len(occs) == 0:
				ui.messageBox('In this design there are no components.')
				return

			fileDialog = ui.createFileDialog()
			fileDialog.isMultiSelectEnabled = False
			fileDialog.title = dialogTitle + " filename"
			fileDialog.filter = 'CSV (*.csv)'
			fileDialog.filterIndex = 0
			dialogResult = fileDialog.showSave()
			if dialogResult == adsk.core.DialogResults.DialogOK:
				filename = fileDialog.filename
			else:
				return

			# Gather information about each unique component
			bom = []
			for occ in occs:
				comp = occ.component
				if comp.name.startswith('_') and prefs["ignoreUnderscorePrefComp"]:
					continue
				elif prefs["ignoreLinkedComp"] and design != comp.parentDesign:
					continue
				elif not comp.bRepBodies.count and prefs["ignoreCompWoBodies"]:
					continue
				elif not occ.isVisible and prefs["ignoreVisibleState"] is False:
					continue
				else:
					jj = 0
					for bomI in bom:
						if bomI['component'] == comp:
							# Increment the instance count of the existing row.
							bomI['instances'] += 1
							break
						jj += 1

					if jj == len(bom):
						# Add this component to the BOM
						bom.append({
							"component": comp,
							"name": comp.name,
							"instances": 1,
							"volume": self.getBodiesVolume(comp.bRepBodies),
							"boundingBox": self.getBodiesBoundingBox(comp.bRepBodies),
							"area": self.getPhysicsArea(comp.bRepBodies),
							"mass": self.getPhysicalMass(comp.bRepBodies),
							"density": self.getPhysicalDensity(comp.bRepBodies),
							"material": self.getPhysicalMaterial(comp.bRepBodies)
						})
			csvStr = self.collectData(design, bom, prefs)
			output = open(filename, 'w')
			output.writelines(csvStr)
			output.close()
			# Save last choosed options
			design.attributes.add(cmdId, "lastUsedOptions", json.dumps(prefs))
			ui.messageBox('File written to "' + filename + '"')
		except:
			if ui:
				ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class BOMCommandInputChangedHandler(adsk.core.InputChangedEventHandler):
	def __init__(self):
		super().__init__()

	def notify(self, args):
		global ui
		global cmdId
		command = args.firingEvent.sender
		inputs = command.commandInputs
		if inputs.itemById(cmdId + "_ignoreUnderscorePrefixedComps").value is True:
			inputs.itemById(cmdId + "_underscorePrefixStrip").isVisible = False
		else:
			inputs.itemById(cmdId + "_underscorePrefixStrip").isVisible = True


def run(context):
	try:
		global ui
		global cmdId
		global dialogTitle
		global cmdDesc
		global cmdRes

		# Get the CommandDefinitions collection.
		cmdDefs = ui.commandDefinitions
		# Create a button command definition.
		bomButton = cmdDefs.addButtonDefinition(cmdId, dialogTitle, cmdDesc, cmdRes)

		# Connect to the command created event.
		commandCreated = BOMCommandCreatedEventHandler()
		bomButton.commandCreated.add(commandCreated)
		handlers.append(commandCreated)

		# Get the ADD-INS panel in the model workspace.
		toolbarPanel = ui.allToolbarPanels.itemById("SolidCreatePanel")

		# Add the button to the bottom of the panel.
		buttonControl = toolbarPanel.controls.addCommand(bomButton, "", False)
		buttonControl.isVisible = True
	except:
		if ui:
			ui.messageBox("Failed:\n{}".format(traceback.format_exc()))


def stop(context):
	try:
		global app
		global ui

		# Clean up the UI.
		cmdDef = ui.commandDefinitions.itemById("CSVBomAddInMenuEntry")
		if cmdDef:
			cmdDef.deleteMe()

		toolbarPanel = ui.allToolbarPanels.itemById("SolidCreatePanel")
		cntrl = toolbarPanel.controls.itemById("CSVBomAddInMenuEntry")
		if cntrl:
			cntrl.deleteMe()
	except:
		if ui:
			ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
