# This script generates a Python interface for an Apple Macintosh Manager.
# It uses the "bgen" package to generate C code.
# The function specifications are generated by scanning the mamager's header file,
# using the "scantools" package (customized for this particular manager).

import string

import addpack
addpack.addpack(':Tools:bgen:bgen')

# Declarations that change for each manager
MACHEADERFILE = 'QuickDraw.h'		# The Apple header file
MODNAME = 'Qd'				# The name of the module
OBJECTNAME = 'Graf'			# The basic name of the objects used here

# The following is *usually* unchanged but may still require tuning
MODPREFIX = MODNAME			# The prefix for module-wide routines
OBJECTTYPE = OBJECTNAME + 'Ptr'		# The C type used to represent them
OBJECTPREFIX = MODPREFIX + 'Obj'	# The prefix for object methods
INPUTFILE = string.lower(MODPREFIX) + 'gen.py' # The file generated by the scanner
EXTRAFILE = string.lower(MODPREFIX) + 'edit.py' # A similar file but hand-made
OUTPUTFILE = MODNAME + "module.c"	# The file generated by this program

from macsupport import *

# Create the type objects

class TextThingieClass(FixedInputBufferType):
	def getargsCheck(self, name):
		pass

TextThingie = TextThingieClass(None)

# These are temporary!
RgnHandle = OpaqueByValueType("RgnHandle", "ResObj")
OptRgnHandle = OpaqueByValueType("RgnHandle", "OptResObj")
PicHandle = OpaqueByValueType("PicHandle", "ResObj")
PolyHandle = OpaqueByValueType("PolyHandle", "ResObj")
PixMapHandle = OpaqueByValueType("PixMapHandle", "ResObj")
PixPatHandle = OpaqueByValueType("PixPatHandle", "ResObj")
PatHandle = OpaqueByValueType("PatHandle", "ResObj")
CursHandle = OpaqueByValueType("CursHandle", "ResObj")
CGrafPtr = OpaqueByValueType("CGrafPtr", "GrafObj")
GrafPtr = OpaqueByValueType("GrafPtr", "GrafObj")
BitMap_ptr = OpaqueByValueType("BitMapPtr", "BMObj")
RGBColor = OpaqueType('RGBColor', 'QdRGB')
RGBColor_ptr = RGBColor

Cursor_ptr = StructInputBufferType('Cursor')
Pattern = StructOutputBufferType('Pattern')
Pattern_ptr = StructInputBufferType('Pattern')
PenState = StructOutputBufferType('PenState')
PenState_ptr = StructInputBufferType('PenState')

includestuff = includestuff + """
#include <%s>""" % MACHEADERFILE + """
#include <Desk.h>

#define resNotFound -192 /* Can't include <Errors.h> because of Python's "errors.h" */

/*
** Parse/generate RGB records
*/
PyObject *QdRGB_New(itself)
	RGBColorPtr itself;
{

	return Py_BuildValue("lll", (long)itself->red, (long)itself->green, (long)itself->blue);
}

QdRGB_Convert(v, p_itself)
	PyObject *v;
	RGBColorPtr p_itself;
{
	long red, green, blue;
	
	if( !PyArg_ParseTuple(v, "lll", &red, &green, &blue) )
		return 0;
	p_itself->red = (unsigned short)red;
	p_itself->green = (unsigned short)green;
	p_itself->blue = (unsigned short)blue;
	return 1;
}

"""

variablestuff = """
{
	PyObject *o;
	
	o = PyString_FromStringAndSize((char *)&qd.arrow, sizeof(qd.arrow));
	if (o == NULL || PyDict_SetItemString(d, "arrow", o) != 0)
		Py_FatalError("can't initialize Qd.arrow");
	o = PyString_FromStringAndSize((char *)&qd.black, sizeof(qd.black));
	if (o == NULL || PyDict_SetItemString(d, "black", o) != 0)
		Py_FatalError("can't initialize Qd.black");
	o = PyString_FromStringAndSize((char *)&qd.white, sizeof(qd.white));
	if (o == NULL || PyDict_SetItemString(d, "white", o) != 0)
		Py_FatalError("can't initialize Qd.white");
	o = PyString_FromStringAndSize((char *)&qd.gray, sizeof(qd.gray));
	if (o == NULL || PyDict_SetItemString(d, "gray", o) != 0)
		Py_FatalError("can't initialize Qd.gray");
	o = PyString_FromStringAndSize((char *)&qd.ltGray, sizeof(qd.ltGray));
	if (o == NULL || PyDict_SetItemString(d, "ltGray", o) != 0)
		Py_FatalError("can't initialize Qd.ltGray");
	o = PyString_FromStringAndSize((char *)&qd.dkGray, sizeof(qd.dkGray));
	if (o == NULL || PyDict_SetItemString(d, "dkGray", o) != 0)
		Py_FatalError("can't initialize Qd.dkGray");
	/* thePort, screenBits and randSeed still missing... */
}
"""

## not yet...
##
##class Region_ObjectDefinition(GlobalObjectDefinition):
##	def outputCheckNewArg(self):
##		Output("if (itself == NULL) return PyMac_Error(resNotFound);")
##	def outputFreeIt(self, itselfname):
##		Output("DisposeRegion(%s);", itselfname)
##
##class Polygon_ObjectDefinition(GlobalObjectDefinition):
##	def outputCheckNewArg(self):
##		Output("if (itself == NULL) return PyMac_Error(resNotFound);")
##	def outputFreeIt(self, itselfname):
##		Output("KillPoly(%s);", itselfname)

class MyGRObjectDefinition(GlobalObjectDefinition):
	def outputCheckNewArg(self):
		Output("if (itself == NULL) return PyMac_Error(resNotFound);")
	def outputCheckConvertArg(self):
		OutLbrace("if (DlgObj_Check(v) || WinObj_Check(v))")
		Output("*p_itself = ((GrafPortObject *)v)->ob_itself;")
		Output("return 1;")
		OutRbrace()
	def outputGetattrHook(self):
		Output("""if ( strcmp(name, "device") == 0 )
			return PyInt_FromLong((long)self->ob_itself->device);
		if ( strcmp(name, "portBits") == 0 ) {
			CGrafPtr itself_color = (CGrafPtr)self->ob_itself;
			
			if ( (itself_color->portVersion&0xc000) == 0xc000 )
				/* XXXX Do we need HLock() stuff here?? */
				return BMObj_New((BitMapPtr)*itself_color->portPixMap);
			else
				return BMObj_New(&self->ob_itself->portBits);
		}
		if ( strcmp(name, "portRect") == 0 )
			return Py_BuildValue("O&", PyMac_BuildRect, &self->ob_itself->portRect);
		/* XXXX Add more, as needed */
		""")

class MyBMObjectDefinition(GlobalObjectDefinition):
	def outputCheckNewArg(self):
		Output("if (itself == NULL) return PyMac_Error(resNotFound);")
	def outputStructMembers(self):
		# We need to more items: a pointer to privately allocated data
		# and a python object we're referring to.
		Output("%s ob_itself;", self.itselftype)
		Output("PyObject *referred_object;")
		Output("BitMap *referred_bitmap;")
	def outputInitStructMembers(self):
		Output("it->ob_itself = %sitself;", self.argref)
		Output("it->referred_object = NULL;")
		Output("it->referred_bitmap = NULL;")
	def outputCleanupStructMembers(self):
		Output("Py_XDECREF(self->referred_object);")
		Output("if (self->referred_bitmap) free(self->referred_bitmap);")
	def outputGetattrHook(self):
		Output("""if ( strcmp(name, "baseAddr") == 0 )
			return PyInt_FromLong((long)self->ob_itself->baseAddr);
		if ( strcmp(name, "rowBytes") == 0 )
			return PyInt_FromLong((long)self->ob_itself->rowBytes);
		if ( strcmp(name, "bounds") == 0 )
			return Py_BuildValue("O&", PyMac_BuildRect, &self->ob_itself->bounds);
		/* XXXX Add more, as needed */
		if ( strcmp(name, "bitmap_data") == 0 )
			return PyString_FromStringAndSize((char *)self->ob_itself, sizeof(BitMap));
		if ( strcmp(name, "pixmap_data") == 0 )
			return PyString_FromStringAndSize((char *)self->ob_itself, sizeof(PixMap));
		""")

# Create the generator groups and link them
module = MacModule(MODNAME, MODPREFIX, includestuff, finalstuff, initstuff, variablestuff)
##r_object = Region_ObjectDefinition('Region', 'QdRgn', 'RgnHandle')
##po_object = Polygon_ObjectDefinition('Polygon', 'QdPgn', 'PolyHandle')
##module.addobject(r_object)
##module.addobject(po_object)
gr_object = MyGRObjectDefinition("GrafPort", "GrafObj", "GrafPtr")
module.addobject(gr_object)
bm_object = MyBMObjectDefinition("BitMap", "BMObj", "BitMapPtr")
module.addobject(bm_object)


# Create the generator classes used to populate the lists
Function = OSErrFunctionGenerator
Method = OSErrMethodGenerator

# Create and populate the lists
functions = []
methods = []
execfile(INPUTFILE)
#execfile(EXTRAFILE)

# add the populated lists to the generator groups
# (in a different wordl the scan program would generate this)
for f in functions: module.add(f)
##for f in r_methods: r_object.add(f)
##for f in po_methods: po_object.add(f)

#
# We manually generate a routine to create a BitMap from python data.
#
BitMap_body = """
BitMap *ptr;
PyObject *source;
Rect bounds;
int rowbytes;
char *data;

if ( !PyArg_ParseTuple(_args, "O!iO&", &PyString_Type, &source, &rowbytes, PyMac_GetRect,
		&bounds) )
	return NULL;
data = PyString_AsString(source);
if ((ptr=(BitMap *)malloc(sizeof(BitMap))) == NULL )
	return PyErr_NoMemory();
ptr->baseAddr = (Ptr)data;
ptr->rowBytes = rowbytes;
ptr->bounds = bounds;
if ( (_res = BMObj_New(ptr)) == NULL ) {
	free(ptr);
	return NULL;
}
((BitMapObject *)_res)->referred_object = source;
Py_INCREF(source);
((BitMapObject *)_res)->referred_bitmap = ptr;
return _res;
"""
	
f = ManualGenerator("BitMap", BitMap_body)
f.docstring = lambda: """Take (string, int, Rect) argument and create BitMap"""
module.add(f)

#
# And again, for turning a correctly-formatted structure into the object
#
RawBitMap_body = """
BitMap *ptr;
PyObject *source;

if ( !PyArg_ParseTuple(_args, "O!", &PyString_Type, &source) )
	return NULL;
if ( PyString_Size(source) != sizeof(BitMap) && PyString_Size(source) != sizeof(PixMap) ) {
	PyErr_BadArgument();
	return NULL;
}
ptr = (BitMapPtr)PyString_AsString(source);
if ( (_res = BMObj_New(ptr)) == NULL ) {
	return NULL;
}
((BitMapObject *)_res)->referred_object = source;
Py_INCREF(source);
return _res;
"""
	
f = ManualGenerator("RawBitMap", RawBitMap_body)
f.docstring = lambda: """Take string BitMap and turn into BitMap object"""
module.add(f)

# generate output (open the output file as late as possible)
SetOutputFileName(OUTPUTFILE)
module.generate()
SetOutputFile() # Close it
