'''dependency'''
from maya import cmds as mc, OpenMaya, OpenMayaUI
import pymel.core as pm
import math, time, os, shiboken, pysideuic
from PySide import QtGui
from cStringIO import StringIO
import xml.etree.ElementTree as xml

path = os.path.dirname(os.path.realpath(__file__)).replace('\\', '/')

def get_maya_window():
	ptr = OpenMayaUI.MQtUtil.mainWindow()
	if ptr is not None:
		return shiboken.wrapInstance(long(ptr), QtGui.QMainWindow)

def load_ui_type(ui_file):
	parsed =  xml.parse(ui_file)
	widget_class = parsed.find('widget').get('class')
	form_class = parsed.find('class').text

	with open(ui_file, 'r') as f:
		o = StringIO()
		frame = {}

		pysideuic.compileUi(f, o, indent=0)
		pyc = compile(o.getvalue(), '<string>', 'exec')
		exec pyc in frame

		form_class = frame['Ui_{0}'.format(form_class)]
		base_class = eval('QtGui.{0}'.format(widget_class))

	return form_class, base_class

def getUV(vtx):
	_vtx = pm.PyNode(vtx)
	u, v = _vtx.getUV()
	return u, v

def vtx_to_follicle(mesh, u, v, name='follicle'):
	follicleShape = mc.createNode('follicle')
	follicleTrans = mc.listRelatives(follicleShape, parent=True)[0]

	follicleTrans = mc.rename(follicleTrans, name)
	follicleShape = mc.rename(mc.listRelatives(follicleTrans, c=True)[0], (name + 'Shape'))
	
	mc.connectAttr(mesh + '.outMesh', follicleShape +  '.inputMesh')    
	mc.connectAttr(mesh + '.worldMatrix[0]', follicleShape +  '.inputWorldMatrix')

	mc.setAttr(follicleShape + '.parameterU', u)    
	mc.setAttr(follicleShape + '.parameterV', v)
	
	mc.connectAttr(follicleShape + '.outRotate', follicleTrans +  '.r')    
	mc.connectAttr(follicleShape + '.outTranslate', follicleTrans + '.t')

	return follicleTrans, follicleShape	

def pw_locator(target=None, const=False, parent=False):
	try:
		temp_shape = mc.createNode("pw_locator", n="TEMPNAME")
		temp_node = mc.listRelatives(temp_shape, parent=True)[0]
		node  = mc.rename(temp_node, 'localDisplay_loc_00')
		shape = mc.rename(temp_shape, '%sShape'%node)
		if target:
			pConstraint = mc.parentConstraint(target, node, mo=False)
			if parent==True:
				mc.parent(node, target)
			elif const==False:
				mc.delete(pConstraint)
		return node, shape
	except:
		mc.warning("Fail to create the pw_display node")
		return None
	
def create_Shape(target, shape ='circle', delete_old_shape=True, scale=1, length=0, color=None):
	available_shapes = ['circle', 'adjustedCube', 'adjustedCylinder', 'poleVector', 'cube', 'settings', 'prism', 'sphere', 'square', 'locator', 'hand', 'banana'] 
	if target:
		old_shape = mc.listRelatives(target, shapes=True)

		if shape in available_shapes:			
			temp_ctrl = mc.file('{0}/Create_Shape/ctrl_templates/{1}.ma'.format(path, shape), i=True, type="mayaAscii", ignoreVersion=True, rnn=True, mergeNamespacesOnClash=False, rpr="temp_ctrl")[0]
			mc.setAttr(temp_ctrl+'.sx', scale)
			mc.setAttr(temp_ctrl+'.sy', scale)
			mc.setAttr(temp_ctrl+'.sz', scale)
			mc.makeIdentity(temp_ctrl, a=True)

			if shape == 'adjustedCube' and length != 0:
				mc.move(length, 0, 0, (temp_ctrl+'.cv[5:6]', temp_ctrl+'.cv[10:15]'), r=True, os=True, wd=True)			
			if shape == 'adjustedCylinder' and length != 0:
				mc.move(length, 0, 0, (temp_ctrl+'.cv[1:6]', temp_ctrl+'.cv[18:33]', temp_ctrl+'.cv[40:45]'), r=True, os=True, wd=True)

			if temp_ctrl:
				shapes = mc.listRelatives(temp_ctrl, shapes=True)
				if shapes:
					for shape in shapes:
						if 0 <= color <= 31:
							mc.setAttr(shape + '.ove', 1)
							mc.setAttr(shape + '.ovc', color)
						
						mc.parent(shape, target, r=True, s=True)
						
					if delete_old_shape and old_shape:
						mc.delete(old_shape)
						
					mc.delete(temp_ctrl)
					
					if len(shapes) == 1:
						mc.rename(target+'|'+shapes[0], target+'Shape')
					else:
						for i, shape in enumerate(shapes):
							mc.rename(target+'|'+shape, target+'Shape'+str(i))
							
def getClosest(pos = (0,0,0), mesh='', debug=False):
	''' return pos, u, v '''
	if mesh == '':
		sel = mc.ls(sl=True)
		if sel:
			mesh = sel[0]
		else: mc.warning('Please select the geometry you wish to connect')
		
	if mc.objExists(mesh) and mc.nodeType(mesh) == 'transform':
		shape = mc.listRelatives(mesh, shapes=True)[0]	
		if shape and mc.nodeType(shape) == 'mesh':
			cpm = mc.createNode('closestPointOnMesh', n='closestPointOnMesh_TEMP')
			mc.connectAttr(shape+'.outMesh', cpm+'.inMesh')
			mc.connectAttr(shape+'.worldMatrix', cpm+'.inputMatrix')

			mc.setAttr(cpm+'.inPositionX', pos[0])
			mc.setAttr(cpm+'.inPositionY', pos[1])
			mc.setAttr(cpm+'.inPositionZ', pos[2])

			pos = mc.getAttr(cpm+'.position')[0]
			u   = mc.getAttr(cpm+'.parameterU')
			v   = mc.getAttr(cpm+'.parameterV')

			mc.delete(cpm)

			if debug:
				print ('pos = '+ str(pos))
				print ('v = '+ str(v))
				print ('u = '+ str(u))

			return pos, u, v

def lockAndHide(target, lockChannels=[]):
	# ex lockChannels = ['ty', 'rx', 'rz', 's', 'v']
	attrLock = []
	for lockChannel in lockChannels:
		if lockChannel in ['t','r','s']:
			for axis in ['x','y','z']:
				at = lockChannel + axis
				attrLock.append(at)
		else:
			attrLock.append(lockChannel)
	for at in attrLock:
		mc.setAttr(target + '.' + at, l = 1, k = 0 )
		
def snap(source, destination, channels = ['t', 'r']):
	# dulicate A
	A_duplicated = mc.duplicate(source, po=1)[0]

	# unlock all duplicate A's attiributes
	for attr  in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']:
		# unlock current attribute
		mc.setAttr((A_duplicated + '.' + attr), l=False)

	# snap duplicated A to B
	mc.delete(mc.parentConstraint(destination, A_duplicated, mo=False))

	attributes = []
	for attr in channels:
		if attr in ['t','r','s']:
			for axis in ['x','y','z']:
				at = attr + axis
				attributes.append(at)
		else:
			attributes.append(attr)
	for at in attributes:
		mc.setAttr(source + '.' + at, mc.getAttr(A_duplicated + '.' + at))

	# delete temp transform
	mc.delete (A_duplicated)

def offset(targetList =[],
			overridePrefix = '',
			parent = '',
			lockChannels = [],
			suffix = '_off',
			name = ''
			):
	try:
		if not targetList:
			targetList = mc.ls(sl=True)
			if not targetList:
				raise Exception, "function: 'offset' - Make sure you specified a target or a valid selection"
				
		offsetGrpList = []
		for target in targetList:
			if not overridePrefix:
				prefix = target
			if not parent:
				oldParent = mc.listRelatives(target, p=True)
				if oldParent:
					parent = oldParent[0]

			if name != '':
				offsetGrp = mc.group(em=True, n=name)
			else:
				offsetGrp = mc.group(em=True, n=prefix + suffix)

			offsetGrpList.append(offsetGrp)
			mc.delete(mc.parentConstraint(target, offsetGrp, mo=False))
			mc.parent(target, offsetGrp)
			if parent and mc.objExists(parent):
				mc.parent(offsetGrp, parent)
			attrLock = []
			for lockChannel in lockChannels:
				if lockChannel in ['t','r','s']:
					for axis in ['x','y','z']:
						at = lockChannel + axis
						attrLock.append(at)
				else:
					attrLock.append(lockChannel)
			for at in attrLock:
				mc.setAttr(offsetGrp + '.' + at, l = 1, k = 0 )
		mc.select(targetList)
		return offsetGrpList
	except:
		mc.warning("/!\ Cannot use Offset command..")

def find_pv(targets=[]):
	# query transforms of the joints
	jnt1Ik_wsT = mc.xform (targets[0], q=True, t=True, ws=True)
	jnt2Ik_wsT = mc.xform (targets[1], q=True, t=True, ws=True)
	jnt3Ik_wsT = mc.xform (targets[2], q=True, t=True, ws=True)
	
	# convert query to MayaVectors
	startVector = OpenMaya.MVector(jnt1Ik_wsT[0], jnt1Ik_wsT[1], jnt1Ik_wsT[2])
	midVector   = OpenMaya.MVector(jnt2Ik_wsT[0], jnt2Ik_wsT[1], jnt2Ik_wsT[2])
	endVector   = OpenMaya.MVector(jnt3Ik_wsT[0], jnt3Ik_wsT[1], jnt3Ik_wsT[2])
	
	startEnd = endVector - startVector
	startMid = midVector - startVector
	
	dotP = startMid * startEnd
	proj = float(dotP)/ float(startEnd.length())
	
	startEndNorm = startEnd.normal()
	
	projVector = startEndNorm * proj
	arrowVector = startMid - projVector
	
	arrowVector *= 0.1
	finalVector = (arrowVector + midVector)
	cross1 = startEnd ^ startMid
	cross1.normalize()
	cross2 = cross1 ^ arrowVector
	cross2.normalize()
			
	matrixVector = [arrowVector.x, arrowVector.y, arrowVector.z, 0,
				   cross1.x, cross1.y, cross1.z, 0,
				   cross2.x, cross2.y, cross2.z, 0,
				   0,0,0,1]

	matrixM = OpenMaya.MMatrix()
	OpenMaya.MScriptUtil.createMatrixFromList (matrixVector, matrixM)
	matrixFinal = OpenMaya.MTransformationMatrix(matrixM)
	rot = matrixFinal.eulerRotation()
	
	simple_pos = [finalVector.x, finalVector.y, finalVector.z]
		
	simple_rot = [(rot.x/math.pi*180.0), (rot.y/math.pi*180.0), (rot.z/math.pi*180.0)]
	return simple_pos, simple_rot

def distance(objA, objB):
	Ax,Ay,Az=mc.xform(objA,q=1,ws=1,t=1)
	Bx,By,Bz=mc.xform(objB,q=1,ws=1,t=1)
	return math.sqrt(pow((Ax-Bx),2)+pow((Ay-By),2)+pow((Az-Bz),2))

def AutoProperties(props):
	class _AutoProperties(type):
		# Inspired by autoprop (http://www.python.org/download/releases/2.2.3/descrintro/)
		def __init__(cls, name, bases, cdict):
			super(_AutoProperties, cls).__init__(name, bases, cdict)
			for attr in props:
				fget=cls._auto_getter(attr)
				fset=cls._auto_setter(attr)
				setattr(cls,attr,property(fget,fset))
	return _AutoProperties

class Vector(object):
	'''Creates a Maya vector/triple, having x, y and z coordinates as float values'''
	__metaclass__=AutoProperties(('x','y','z'))
	def __init__(self, x=0, y=0, z=0):
		# I assume you want the initial values to be converted to floats too.
		self._x, self._y, self._z = map(float,(x, y, z))
	@staticmethod
	def _auto_setter(attr):
		def set_float(self, value):
			setattr(self, '_'+attr, float(value))
		return set_float
	@staticmethod   
	def _auto_getter(attr):
		def get_float(self):
			return getattr(self, '_'+attr)
		return get_float
	
def wait(secs=0.05):
	time.sleep(secs)
	mc.refresh()

def mirror(target):
	mc.setAttr(target+'.sx', -mc.getAttr(target +'.sx'))
	mc.setAttr(target+'.rx', 180 + mc.getAttr(target+'.rx'))

def snapOnCurve(target, crv, u=0, closestPoint=False, cp=False):
	closestPoint = cp and closestPoint
	if not 0<=u<=1:
		mc.warning('u should be between 0 and 1')
		return
	curveShape = mc.listRelatives(crv, shapes=True)[0]
	motionpath = mc.createNode('motionPath', n='TEMP_motionPath_00')
	mc.setAttr('%s.fractionMode'%motionpath, True)
	mc.connectAttr('%s.worldSpace[0]'%curveShape, '%s.geometryPath'%motionpath)
	mc.connectAttr('%s.allCoordinates'%motionpath, '%s.translate'%target)
	if closestPoint:
		u = getUParam(mc.xform(target, q=True, t=True, ws=True), crv)
	mc.setAttr('%s.uValue'%motionpath, u)
	pos = mc.xform(target, q=True, t=True, ws=True)
	mc.delete(motionpath)
	mc.xform(target, t=pos, ws=True)

def getUParam(pnt=[], crv=None):
	point = OpenMaya.MPoint(pnt[0],pnt[1],pnt[2])
	curveFn = OpenMaya.MFnNurbsCurve(getDagPath(crv))
	paramUtill=OpenMaya.MScriptUtil()
	paramPtr=paramUtill.asDoublePtr()
	isOnCurve = curveFn.isPointOnCurve(point)
	if isOnCurve == True:        
		curveFn.getParamAtPoint(point , paramPtr,0.001,OpenMaya.MSpace.kObject )
	else :
		point = curveFn.closestPoint(point,paramPtr,0.001,OpenMaya.MSpace.kObject)
		curveFn.getParamAtPoint(point, paramPtr,0.001,OpenMaya.MSpace.kObject )
	
	param = paramUtill.getDouble(paramPtr)  
	return param

def getDagPath(objectName):    
	if isinstance(objectName, list)==True:
		oNodeList=[]
		for o in objectName:
			selectionList = OpenMaya.MSelectionList()
			selectionList.add(o)
			oNode = OpenMaya.MDagPath()
			selectionList.getDagPath(0, oNode)
			oNodeList.append(oNode)
		return oNodeList
	else:
		selectionList = OpenMaya.MSelectionList()
		selectionList.add(objectName)
		oNode = OpenMaya.MDagPath()
		selectionList.getDagPath(0, oNode)
		return oNode
