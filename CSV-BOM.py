#Author-Peter Boeker
#Description-Provides customizable prefixes to collect browser components with there boundary box dimention or volume.

import adsk.core
import adsk.fusion
import adsk.cam
import traceback
import json
import re

# Global list to keep all event handlers in scope.
# This is only needed with Python.
handlers = []
app = adsk.core.Application.get()
ui = app.userInterface
cmdId = "CSVBomAddInMenuEntry"
cmdName = "CSV-BOM"
dialogTitle = "Create BOM"
cmdDesc = "Creates a bill of material and a cutlist from the browser components."
cmdRes = ".//resources//CSV-BOM"

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
		_splitDims = True
		_sortDims = False
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
		_generateCutList = False
		_includeDesc = False
		_useComma = False
		if lastPrefs:
			try:
				lastPrefs = json.loads(lastPrefs.value)
				_onlySelectedComps = lastPrefs.get("onlySelComp", False)
				_includeBoundingboxDims = lastPrefs.get("incBoundDims", True)
				_splitDims = lastPrefs.get("splitDims", True)
				_sortDims = lastPrefs.get("sortDims", False)
				_ignoreUnderscorePrefixedComps = lastPrefs.get("ignoreUnderscorePrefComp", True)
				_underscorePrefixStrip = lastPrefs.get("underscorePrefixStrip", False)
				_ignoreCompsWithoutBodies = lastPrefs.get("ignoreCompWoBodies", True)
				_ignoreLinkedComps = lastPrefs.get("ignoreLinkedComp", True)
				_ignoreVisibleState = lastPrefs.get("ignoreVisibleState", True)
				_includeVolume = lastPrefs.get("incVol", False)
				_includeArea = lastPrefs.get("incArea", False)
				_includeMass = lastPrefs.get("incMass", False)
				_includeDensity = lastPrefs.get("incDensity", False)
				_includeMaterial = lastPrefs.get("incMaterial", False)
				_generateCutList = lastPrefs.get("generateCutList", False)
				_includeDesc = lastPrefs.get("incDesc", False)
				_useComma = lastPrefs.get("useComma", False)
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

		ipSplitDims = inputs.addBoolValueInput(cmdId + "_splitDims", "Separate dimension", True, "", _splitDims)
		ipSplitDims.tooltip = "Places the dimension values in separate CVS output columns."
		ipSplitDims.isVisible = _includeBoundingboxDims

		ipsortDims = inputs.addBoolValueInput(cmdId + "_sortDims", "Sort dimensions", True, "", _sortDims)
		ipsortDims.tooltip = "Sorts the dimensions for working with panels. The smallest value becomes the height (thickness), the next larger the width and the largest the length."
		ipsortDims.isVisible = _includeBoundingboxDims

		ipUnderscorePrefix = inputs.addBoolValueInput(cmdId + "_ignoreUnderscorePrefixedComps", 'Exclude "_"', True, "", _ignoreUnderscorePrefixedComps)
		ipUnderscorePrefix.tooltip = 'Exclude all components there name starts with "_"'

		ipUnderscorePrefixStrip = inputs.addBoolValueInput(cmdId + "_underscorePrefixStrip", 'Strip "_"', True, "", _underscorePrefixStrip)
		ipUnderscorePrefixStrip.tooltip = 'If checked, "_" is stripped from components name'
		ipUnderscorePrefixStrip.isVisible = not _ignoreUnderscorePrefixedComps

		ipWoBodies = inputs.addBoolValueInput(cmdId + "_ignoreCompsWithoutBodies", "Exclude if no bodies", True, "", _ignoreCompsWithoutBodies)
		ipWoBodies.tooltip = "Exclude all components if they have at least one body"

		ipLinkedComps = inputs.addBoolValueInput(cmdId + "_ignoreLinkedComps", "Exclude linked", True, "", _ignoreLinkedComps)
		ipLinkedComps.tooltip = "Exclude all components they are linked into the design"

		ipVisibleState = inputs.addBoolValueInput(cmdId + "_ignoreVisibleState", "Ignore visible state", True, "", _ignoreVisibleState)
		ipVisibleState.tooltip = "Ignores the visible state for components"

		grpPhysics = inputs.addGroupCommandInput(cmdId + "_grpPhysics", "Additional Physics")
		if _includeVolume or _includeArea or _includeMass or _includeDensity or _includeMaterial:
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

		grpCutList = inputs.addGroupCommandInput(cmdId + "_grpCutList", "Cut List")
		if _generateCutList:
			grpCutList.isExpanded = True
		else:
			grpCutList.isExpanded = False
		grpCutList.isVisible = _includeBoundingboxDims
		grpCutListChildren = grpCutList.children

		ipGenerateCutList = grpCutListChildren.addBoolValueInput(cmdId + "_generateCutList", "Generate Cut List", True, "", _generateCutList)
		ipGenerateCutList.tooltip = "Generates a file for the cut list optimization program from Gary Darby."

		grpMisc = inputs.addGroupCommandInput(cmdId + "_grpMisc", "Misc")
		if (_includeDesc or _useComma):
			grpMisc.isExpanded = True
		else:
			grpMisc.isExpanded = False
		grpMiscChildren = grpMisc.children
		ipCompDesc = grpMiscChildren.addBoolValueInput(cmdId + "_includeCompDesc", "Include description", True, "", _includeDesc)
		ipCompDesc.tooltip = "Includes the component description. You can add a description<br/>by right clicking a component and open the Properties panel."

		ipUseComma = grpMiscChildren.addBoolValueInput(cmdId + "_useComma", "Use comma delimiter", True, "", _useComma)
		ipUseComma.tooltip = "Uses comma instead of point for number decimal delimiter."

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

	def replacePointDelimterOnPref(self, pref, value):
		if (pref):
			return str(value).replace(".", ",")
		return str(value)

	def collectData(self, design, bom, prefs):
		csvStr = ''
		defaultUnit = design.fusionUnitsManager.defaultLengthUnits
		csvHeader = ["Part name", "Quantity"]
		if prefs["incVol"]:
			csvHeader.append("Volume cm^3")
		if prefs["incBoundDims"]:
			if prefs["splitDims"]:
				csvHeader.append("Width " + defaultUnit)
				csvHeader.append("Length " + defaultUnit)
				csvHeader.append("Height " + defaultUnit)
			else:
				csvHeader.append("Dimension " + defaultUnit)
		if prefs["incArea"]:
			csvHeader.append("Area cm^2")
		if prefs["incMass"]:
			csvHeader.append("Mass kg")
		if prefs["incDensity"]:
			csvHeader.append("Density kg/cm^2")
		if prefs["incMaterial"]:
			csvHeader.append("Material")
		if prefs["incDesc"]:
			csvHeader.append("Description")
		for k in csvHeader:
			csvStr += '"' + k + '",'
		csvStr += '\n'
		for item in bom:
			dims = ''
			name = self.filterFusionCompNameInserts(item["name"])
			if prefs["ignoreUnderscorePrefComp"] is False and prefs["underscorePrefixStrip"] is True and name[0] == '_':
				name = name[1:]
			csvStr += '"' + name + '","' + self.replacePointDelimterOnPref(prefs["useComma"], item["instances"]) + '",'
			if prefs["incVol"]:
				csvStr += '"' + self.replacePointDelimterOnPref(prefs["useComma"], item["volume"]) + '",'
			if prefs["incBoundDims"]:
				dim = 0
				footInchDispFormat = app.preferences.unitAndValuePreferences.footAndInchDisplayFormat
				
				for k in item["boundingBox"]:
					dim += item["boundingBox"][k]
				if dim > 0:
					if footInchDispFormat == 0:
						dimX = float(design.fusionUnitsManager.formatInternalValue(item["boundingBox"]["x"], defaultUnit, False))
						dimY = float(design.fusionUnitsManager.formatInternalValue(item["boundingBox"]["y"], defaultUnit, False))
						dimZ = float(design.fusionUnitsManager.formatInternalValue(item["boundingBox"]["z"], defaultUnit, False))
						if prefs["sortDims"]:
							dimSorted = sorted([dimX, dimY, dimZ])
							bbZ = "{0:.3f}".format(dimSorted[0])
							bbX = "{0:.3f}".format(dimSorted[1])
							bbY = "{0:.3f}".format(dimSorted[2])
						else:
							bbX = "{0:.3f}".format(dimX)
							bbY = "{0:.3f}".format(dimY)
							bbZ = "{0:.3f}".format(dimZ)
	
						if prefs["splitDims"]:
							csvStr += '"' + self.replacePointDelimterOnPref(prefs["useComma"], bbX) + '",'
							csvStr += '"' + self.replacePointDelimterOnPref(prefs["useComma"], bbY) + '",'
							csvStr += '"' + self.replacePointDelimterOnPref(prefs["useComma"], bbZ) + '",'
						else:
							dims += '"' + self.replacePointDelimterOnPref(prefs["useComma"], bbX) + ' x '
							dims += self.replacePointDelimterOnPref(prefs["useComma"], bbY) + ' x '
							dims += self.replacePointDelimterOnPref(prefs["useComma"], bbZ)
							csvStr += dims + '",'
					else:
						dimX = design.fusionUnitsManager.formatInternalValue(item["boundingBox"]["x"], defaultUnit, False)
						dimY = design.fusionUnitsManager.formatInternalValue(item["boundingBox"]["y"], defaultUnit, False)
						dimZ = design.fusionUnitsManager.formatInternalValue(item["boundingBox"]["z"], defaultUnit, False)

						if prefs["splitDims"]:
							csvStr += '"' + dimX + '",'
							csvStr += '"' + dimY + '",'
							csvStr += '"' + dimZ + '",'
						else:
							dims += '"' + dimX + ' x '
							dims += dimY + ' x '
							dims += dimZ
							csvStr += dims + '",'						
				else:
					if prefs["splitDims"]:
						csvStr += "0" + ','
						csvStr += "0" + ','
						csvStr += "0" + ','
					else:
						csvStr += "0" + ','
			if prefs["incArea"]:
				csvStr += '"' + self.replacePointDelimterOnPref(prefs["useComma"], "{0:.2f}".format(item["area"])) + '",'
			if prefs["incMass"]:
				csvStr += '"' + self.replacePointDelimterOnPref(prefs["useComma"], "{0:.5f}".format(item["mass"])) + '",'
			if prefs["incDensity"]:
				csvStr += '"' + self.replacePointDelimterOnPref(prefs["useComma"], "{0:.5f}".format(item["density"])) + '",'
			if prefs["incMaterial"]:
				csvStr += '"' + item["material"] + '",'
			if prefs["incDesc"]:
				csvStr += '"' + item["desc"] + '",'
			csvStr += '\n'
		return csvStr

	def collectCutList(self, design, bom, prefs):
		defaultUnit = design.fusionUnitsManager.defaultLengthUnits

		# Init CutList Header
		cutListStr = 'V2\n'
		if prefs["useComma"]:
			cutListStr += 'FormatSettings.decimalseparator,\n'
		else:
			cutListStr += 'FormatSettings.decimalseparator.\n'
		cutListStr += '\n'
		cutListStr += 'Required\n'

		#add parts:
		for item in bom:
			name = self.filterFusionCompNameInserts(item["name"])
			if prefs["ignoreUnderscorePrefComp"] is False and prefs["underscorePrefixStrip"] is True and name[0] == '_':
				name = name[1:]
			# dimensions:
			dim = 0
			for k in item["boundingBox"]:
				dim += item["boundingBox"][k]
			if dim > 0:
				dimX = float(design.fusionUnitsManager.formatInternalValue(item["boundingBox"]["x"], defaultUnit, False))
				dimY = float(design.fusionUnitsManager.formatInternalValue(item["boundingBox"]["y"], defaultUnit, False))
				dimZ = float(design.fusionUnitsManager.formatInternalValue(item["boundingBox"]["z"], defaultUnit, False))

				if prefs["sortDims"]:
					dims = sorted([dimX, dimY, dimZ])
				else:
					dims = [dimZ, dimX, dimY]

				partStr = ' '  # leading space
				partStr += self.replacePointDelimterOnPref(prefs["useComma"], "{0:.3f}".format(dims[1])).ljust(9)  # width
				partStr += self.replacePointDelimterOnPref(prefs["useComma"], "{0:.3f}".format(dims[2])).ljust(7)  # length

				partStr += name
				partStr += ' (thickness: ' + self.replacePointDelimterOnPref(prefs["useComma"], "{0:.3f}".format(dims[0])) + defaultUnit + ')'
				partStr += '\n'

			else:
				partStr = ' 0        0      ' + name + '\n'

			# add all instances of the component to the CutList:
			quantity = int(item["instances"])
			for i in range(0, quantity):
				cutListStr += partStr

		# empty entry for available materials (sheets):
		cutListStr += '\n' + "Available" + '\n'

		return cutListStr

	def getPrefsObject(self, inputs):
		obj = {
			"onlySelComp": inputs.itemById(cmdId + "_onlySelectedComps").value,
			"incBoundDims": inputs.itemById(cmdId + "_includeBoundingboxDims").value,
			"splitDims": inputs.itemById(cmdId + "_splitDims").value,
			"sortDims": inputs.itemById(cmdId + "_sortDims").value,
			"ignoreUnderscorePrefComp": inputs.itemById(cmdId + "_ignoreUnderscorePrefixedComps").value,
			"underscorePrefixStrip": inputs.itemById(cmdId + "_underscorePrefixStrip").value,
			"ignoreCompWoBodies": inputs.itemById(cmdId + "_ignoreCompsWithoutBodies").value,
			"ignoreLinkedComp": inputs.itemById(cmdId + "_ignoreLinkedComps").value,
			"ignoreVisibleState": inputs.itemById(cmdId + "_ignoreVisibleState").value,
			"incVol": inputs.itemById(cmdId + "_includeVolume").value,
			"incArea": inputs.itemById(cmdId + "_includeArea").value,
			"incMass": inputs.itemById(cmdId + "_includeMass").value,
			"incDensity": inputs.itemById(cmdId + "_includeDensity").value,
			"incMaterial": inputs.itemById(cmdId + "_includeMaterial").value,
			"generateCutList": inputs.itemById(cmdId + "_generateCutList").value,
			"incDesc": inputs.itemById(cmdId + "_includeCompDesc").value,
			"useComma": inputs.itemById(cmdId + "_useComma").value
		}
		return obj

	def getBodiesVolume(self, bodies):
		volume = 0
		for bodyK in bodies:
			if bodyK.isSolid:
				volume += bodyK.volume
		return volume

	# Calculates a tight bounding box around the input body.  An optional
	# tolerance argument is available.  This specificies the tolerance in
	# centimeters.  If not provided the best existing display mesh is used.
	def calculateTightBoundingBox(self, body, tolerance=0):
		try:
			# If the tolerance is zero, use the best display mesh available.
			if tolerance <= 0:
				# Get the best display mesh available.
				triMesh = body.meshManager.displayMeshes.bestMesh
			else:
				# Calculate a new mesh based on the input tolerance.
				meshMgr = adsk.fusion.MeshManager.cast(body.meshManager)
				meshCalc = meshMgr.createMeshCalculator()
				meshCalc.surfaceTolerance = tolerance
				triMesh = meshCalc.calculate()

			# Calculate the range of the mesh.
			smallPnt = adsk.core.Point3D.cast(triMesh.nodeCoordinates[0])
			largePnt = adsk.core.Point3D.cast(triMesh.nodeCoordinates[0])
			vertex = adsk.core.Point3D.cast(None)
			for vertex in triMesh.nodeCoordinates:
				if vertex.x < smallPnt.x:
					smallPnt.x = vertex.x

				if vertex.y < smallPnt.y:
					smallPnt.y = vertex.y

				if vertex.z < smallPnt.z:
					smallPnt.z = vertex.z

				if vertex.x > largePnt.x:
					largePnt.x = vertex.x

				if vertex.y > largePnt.y:
					largePnt.y = vertex.y

				if vertex.z > largePnt.z:
					largePnt.z = vertex.z

			# Create and return a BoundingBox3D as the result.
			return(adsk.core.BoundingBox3D.create(smallPnt, largePnt))
		except:
			# An error occurred so return None.
			return None

	def getBodiesBoundingBox(self, bodies):
		minPointX = maxPointX = minPointY = maxPointY = minPointZ = maxPointZ = 0
		# Examining the maximum min point distance and the maximum max point distance.
		for body in bodies:
			if body.isSolid:
				bb = self.calculateTightBoundingBox(body, 0)
				if not bb:
					return None
				if not minPointX or bb.minPoint.x < minPointX:
					minPointX = bb.minPoint.x
				if not maxPointX or bb.maxPoint.x > maxPointX:
					maxPointX = bb.maxPoint.x
				if not minPointY or bb.minPoint.y < minPointY:
					minPointY = bb.minPoint.y
				if not maxPointY or bb.maxPoint.y > maxPointY:
					maxPointY = bb.maxPoint.y
				if not minPointZ or bb.minPoint.z < minPointZ:
					minPointZ = bb.minPoint.z
				if not maxPointZ or bb.maxPoint.z > maxPointZ:
					maxPointZ = bb.maxPoint.z
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

	def filterFusionCompNameInserts(self, name):
		name = re.sub("\([0-9]+\)$", '', name)
		name = name.strip()
		name = re.sub("v[0-9]+$", '', name)
		return name.strip()

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
						bb = self.getBodiesBoundingBox(comp.bRepBodies)
						if not bb:
							if ui:
								ui.messageBox('Not all Fusion modules are loaded yet, please click on the root component to load them and try again.')
							return

						bom.append({
							"component": comp,
							"name": comp.name,
							"instances": 1,
							"volume": self.getBodiesVolume(comp.bRepBodies),
							"boundingBox": bb,
							"area": self.getPhysicsArea(comp.bRepBodies),
							"mass": self.getPhysicalMass(comp.bRepBodies),
							"density": self.getPhysicalDensity(comp.bRepBodies),
							"material": self.getPhysicalMaterial(comp.bRepBodies),
							"desc": comp.description
						})
			csvStr = self.collectData(design, bom, prefs)
			output = open(filename, 'w')
			output.writelines(csvStr)
			output.close()

			# save CutList:
			if prefs["generateCutList"] and prefs["incBoundDims"]:
				cutListStr = self.collectCutList(design, bom, prefs)
				output = open(filename[:len(filename) - 4] + '_cutList.txt', 'w')
				output.write(cutListStr)
				output.close()

			# Save last chosen options
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
		if inputs.itemById(cmdId + "_includeBoundingboxDims").value is True:
			inputs.itemById(cmdId + "_splitDims").isVisible = True
			inputs.itemById(cmdId + "_sortDims").isVisible = True
			inputs.itemById(cmdId + "_grpCutList").isVisible = True
		else:
			inputs.itemById(cmdId + "_splitDims").isVisible = False
			inputs.itemById(cmdId + "_sortDims").isVisible = False
			inputs.itemById(cmdId + "_grpCutList").isVisible = False

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
