from abc import ABCMeta, abstractmethod
from pywps._compat import text_type, StringIO
import tempfile, os
from pywps.inout.literaltypes import LITERAL_DATA_TYPES
from pywps import OWS, OGCUNIT, NAMESPACES
from pywps import configuration
from pywps.exceptions import InvalidParameterValue
import base64


class SOURCE_TYPE:
    MEMORY = 0
    FILE = 1
    STREAM = 2
    DATA = 3

class DataTypeAbstract(object):
    """LiteralObject data_type abstract class
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def convert(self, value):
        return value


class IOHandler(object):
    """Basic IO class. Provides functions, to accept input data in file,
    memory object and stream object and give them out in all three types

    >>> # setting up 
    >>> import os
    >>> from io import RawIOBase
    >>> from io import FileIO
    >>> import types
    >>>
    >>> ioh_file = IOHandler(workdir=tmp)
    >>> assert isinstance(ioh_file, IOHandler)
    >>>
    >>> # Create test file input
    >>> fileobj = open(os.path.join(tmp, 'myfile.txt'), 'w')
    >>> fileobj.write('ASDF ASFADSF ASF ASF ASDF ASFASF')
    >>> fileobj.close()
    >>>
    >>> # testing file object on input
    >>> ioh_file.file = fileobj.name
    >>> assert ioh_file.source_type == SOURCE_TYPE.FILE
    >>> file = ioh_file.file
    >>> stream = ioh_file.stream
    >>>
    >>> assert file == fileobj.name
    >>> assert isinstance(stream, RawIOBase)
    >>> # skipped assert isinstance(ioh_file.memory_object, POSH)
    >>>
    >>> # testing stream object on input
    >>> ioh_stream = IOHandler(workdir=tmp)
    >>> assert ioh_stream.workdir == tmp
    >>> ioh_stream.stream = FileIO(fileobj.name,'r')
    >>> assert ioh_stream.source_type == SOURCE_TYPE.STREAM
    >>> file = ioh_stream.file
    >>> stream = ioh_stream.stream
    >>>
    >>> assert open(file).read() == ioh_file.stream.read()
    >>> assert isinstance(stream, RawIOBase)
    >>> # skipped assert isinstance(ioh_stream.memory_object, POSH)
    >>>
    >>> # testing in memory object object on input
    >>> # skipped ioh_mo = IOHandler(workdir=tmp)
    >>> # skipped ioh_mo.memory_object = POSH
    >>> # skipped assert ioh_mo.source_type == SOURCE_TYPE.MEMORY
    >>> # skipped file = ioh_mo.file
    >>> # skipped stream = ioh_mo.stream
    >>> # skipped posh = ioh_mo.memory_object
    >>> #
    >>> # skipped assert open(file).read() == ioh_file.stream.read()
    >>> # skipped assert isinstance(ioh_mo.stream, RawIOBase)
    >>> # skipped assert isinstance(ioh_mo.memory_object, POSH)
    """

    def __init__(self, workdir=None):
        self.source_type = None
        self.source = None
        self._tempfile = None
        self.workdir = workdir

    def set_file(self, filename):
        """Set source as file name"""
        self.source_type = SOURCE_TYPE.FILE
        self.source = os.path.abspath(filename)

    def set_workdir(self, workdirpath):
        """Set working temporary directory for files to be stored in"""

        if workdirpath is not None and not os.path.exists(workdirpath):
            os.makedirs(workdirpath)

        self._workdir = workdirpath


    def set_memory_object(self, memory_object):
        """Set source as in memory object"""
        self.source_type = SOURCE_TYPE.MEMORY

    def set_stream(self, stream):
        """Set source as stream object"""
        self.source_type = SOURCE_TYPE.STREAM
        self.source = stream

    def set_data(self, data):
        """Set source as simple datatype e.g. string, number"""
        self.source_type = SOURCE_TYPE.DATA
        self.source = data

    def set_base64(self, data):
        """Set data encoded in base64"""

        self.data = base64.b64decode(data)

    def get_file(self):
        """Get source as file name"""
        if self.source_type == SOURCE_TYPE.FILE:
            return self.source

        elif self.source_type == SOURCE_TYPE.STREAM or\
             self.source_type == SOURCE_TYPE.DATA:

            if self._tempfile:
                return self._tempfile
            else:
                (opening, stream_file_name) = tempfile.mkstemp(dir=self.workdir)
                stream_file = open(stream_file_name, 'w')

                if self.source_type == SOURCE_TYPE.STREAM:
                    stream_file.write(self.source.read())
                else:
                    stream_file.write(self.source)

                stream_file.close()
                self._tempfile = str(stream_file_name)
                return self._tempfile

    def get_workdir(self):
        """Return working directory name
        """
        return self._workdir

    def get_memory_object(self):
        """Get source as memory object"""
        raise Exception("setmemory_object not implemented, Soeren promissed to implement at WPS Workshop on 23rd of January 2014")

    def get_stream(self):
        """Get source as stream object"""
        if self.source_type == SOURCE_TYPE.FILE:
            from io import FileIO
            return FileIO(self.source, mode='r', closefd=True)
        elif self.source_type == SOURCE_TYPE.STREAM:
            return self.source
        elif self.source_type == SOURCE_TYPE.DATA:
            return StringIO(text_type(self.source))

    def get_data(self):
        """Get source as simple data object"""
        if self.source_type == SOURCE_TYPE.FILE:
            file_handler = open(self.source, mode='r')
            content = file_handler.read()
            file_handler.close()
            return content
        elif self.source_type == SOURCE_TYPE.STREAM:
            return self.source.read()
        elif self.source_type == SOURCE_TYPE.DATA:
            return self.source

    def get_base64(self):
        return base64.b64encode(self.data)

    # Properties
    file = property(fget=get_file, fset=set_file)
    memory_object = property(fget=get_memory_object, fset=set_memory_object)
    stream = property(fget=get_stream, fset=set_stream)
    data = property(fget=get_data, fset=set_data)
    base64 = property(fget=get_base64, fset=set_base64)
    workdir = property(fget=get_workdir, fset=set_workdir)


class SimpleHandler(IOHandler):
    """Data handler for Literal In- and Outputs

    >>> class Int_type(object):
    ...     @staticmethod
    ...     def convert(value): return int(value)
    >>>
    >>> class MyValidator(object):
    ...     @staticmethod
    ...     def validate(inpt): return 0 < inpt.data < 3
    >>>
    >>> inpt = SimpleHandler(data_type = Int_type)
    >>> inpt.validator = MyValidator
    >>>
    >>> inpt.data = 1
    >>> inpt.validator.validate(inpt)
    True
    >>> inpt.data = 5
    >>> inpt.validator.validate(inpt)
    False
    """

    def __init__(self, workdir=None, data_type=None):
        IOHandler.__init__(self, workdir)
        self.data_type = data_type
        self._validator = None

    def get_data(self):
        return IOHandler.get_data(self)

    def set_data(self, data):
        """Set data value. input data are converted into target format
        """
        if self.data_type:
            # TODO: check datatypeabstract class somethings missing here
            # check if it is a valid data_type
            if self.data_type.lower() in LITERAL_DATA_TYPES:
                if self.data_type.lower() == 'string':
                    data = text_type(data)
                elif self.data_type.lower() == 'integer':
                    data = int(data)
                elif self.data_type.lower() == 'float':
                    data = float(data)
                elif self.data_type.lower() == 'boolean':
                    if data.lower() == 'true':
                        data = True
                    else:
                        data = False
                #data = self.data_type.convert(data)

                IOHandler.set_data(self, data)

    @property
    def validator(self):
        return self._validator

    @validator.setter
    def validator(self, validator):
        self._validator = validator

    data = property(fget=get_data, fset=set_data)


class BasicIO:
    """Basic Input or Ouput class
    """
    def __init__(self, identifier, title=None, abstract=None):
        self.identifier = identifier
        self.title = title
        self.abstract = abstract

class BasicLiteral:
    """Basic literal input/output class
    """

    def __init__(self, data_type=None, uoms=None):
        if not data_type:
            data_type = LITERAL_DATA_TYPES[2]
        assert data_type in LITERAL_DATA_TYPES
        self.data_type = data_type
        self.uoms = None
        self._uom = None

        if self.uoms:
            self.uom = self.uoms[0]

        if uoms:
            if type(uoms) is not type([]):
                uoms = [uoms]

            self.uoms = []
            for uom in uoms:
                if not isinstance(uom, UOM):
                    uom = UOM(uom)
                self.uoms.append(uom)

    @property
    def uom(self):
        return self._uom

    @uom.setter
    def uom(self, uom):
        self._uom = uom


class BasicComplex(object):
    """Basic complex input/output class
    """

    def __init__(self, data_format=None, supported_formats=None):
        self._data_format = None
        self.supported_formats = supported_formats
        if self.supported_formats:
            self.data_format = supported_formats[0]
        if data_format:
            self.data_format = data_format

    @property
    def data_format(self):
        return self._data_format


    @data_format.setter
    def data_format(self, data_format):
        """self data_format setter
        """
        if self._is_supported(data_format):
            self._data_format = data_format
        else:
            raise InvalidParameterValue("Requested format "
                                        "%s, %s, %s not supported" %\
                                        (data_format.mime_type,
                                         data_format.encoding,
                                         data_format.schema))

    def _is_supported(self, data_format):

        for frmt in self.supported_formats:
            if frmt.same_as(data_format):
                return True

        return False

        

class BasicBoundingBox(object):
    """Basic BoundingBox input/output class
    """

    def __init__(self, crss=None, dimensions=2):
        self.crss = crss or ['epsg:4326']
        self.crs = self.crss[0]
        self.dimensions = dimensions
        self.ll = []
        self.ur = []

class LiteralInput(BasicIO, BasicLiteral, SimpleHandler):
    """LiteralInput input abstract class
    """

    def __init__(self, identifier, title=None, abstract=None,
                 data_type=None, workdir=None, allowed_values=None, uoms=None):
        BasicIO.__init__(self, identifier, title, abstract)
        BasicLiteral.__init__(self, data_type, uoms)
        SimpleHandler.__init__(self, workdir, data_type)

        self.allowed_values = allowed_values
        self.any_value = self.allowed_values is None


class LiteralOutput(BasicIO, BasicLiteral, SimpleHandler):
    """Basic LiteralOutput class
    """

    def __init__(self, identifier, title=None, abstract=None,
                 data_type=None, workdir=None, uoms=None):
        BasicIO.__init__(self, identifier, title, abstract)
        BasicLiteral.__init__(self, data_type, uoms)
        SimpleHandler.__init__(self, workdir=None, data_type=data_type)

        self._storage = None

    @property
    def storage(self):
        return self._storage

    @storage.setter
    def storage(self, storage):
        self._storage = storage

class BBoxInput(BasicIO, BasicBoundingBox, IOHandler):
    """Basic Bounding box input abstract class
    """

    def __init__(self, identifier, title=None, abstract=None, crss=None,
            dimensions=None, workdir=None):
        BasicIO.__init__(self, identifier, title, abstract)
        BasicBoundingBox.__init__(self, crss, dimensions)
        IOHandler.__init__(self, workdir=None)

class BBoxOutput(BasicIO, BasicBoundingBox, SimpleHandler):
    """Basic BoundingBox output class
    """

    def __init__(self, identifier, title=None, abstract=None, crss=None,
            dimensions=None, workdir=None):
        BasicIO.__init__(self, identifier, title, abstract)
        BasicBoundingBox.__init__(self, crss, dimensions)
        SimpleHandler.__init__(self, workdir=None)
        self._storage = None

    @property
    def storage(self):
        return self._storage

    @storage.setter
    def storage(self, storage):
        self._storage = storage


class ComplexInput(BasicIO, BasicComplex, IOHandler):
    """Complex input abstract class

    >>> ci = ComplexInput()
    >>> ci.validator = 1
    >>> ci.validator
    1
    """

    def __init__(self, identifier, title=None, abstract=None,
                 workdir=None, data_format=None, supported_formats=None):
        BasicIO.__init__(self, identifier, title, abstract)
        BasicComplex.__init__(self, data_format, supported_formats)
        IOHandler.__init__(self, workdir)



class ComplexOutput(BasicIO, BasicComplex, IOHandler):
    """Complex output abstract class

    >>> # temporary configuration
    >>> import ConfigParser
    >>> from pywps.storage import *
    >>> config = ConfigParser.RawConfigParser()
    >>> config.add_section('FileStorage')
    >>> config.set('FileStorage', 'target', './')
    >>> config.add_section('server')
    >>> config.set('server', 'outputurl', 'http://foo/bar/filestorage')
    >>>
    >>> # create temporary file
    >>> tiff_file = open('file.tiff', 'w')
    >>> tiff_file.write("AA")
    >>> tiff_file.close()
    >>>
    >>> co = ComplexOutput()
    >>> co.set_file('file.tiff')
    >>> fs = FileStorage(config)
    >>> co.storage = fs
    >>>
    >>> url = co.get_url() # get url, data are stored
    >>>
    >>> co.get_stream().read() # get data - nothing is stored
    'AA'
    """

    def __init__(self, identifier, title=None, abstract=None,
                 workdir=None, data_format=None, supported_formats=None):
        BasicIO.__init__(self, identifier, title, abstract)
        BasicComplex.__init__(self, data_format, supported_formats)
        IOHandler.__init__(self, workdir)

        self._storage = None

    @property
    def storage(self):
        return self._storage

    @storage.setter
    def storage(self, storage):
        self._storage = storage

    def get_url(self):
        """Return URL pointing to data
        """
        (outtype, storage, url) = self.storage.store(self)
        return url


class UOM(object):
    """
    :param uom: unit of measure
    """

    def __init__(self, uom=''):
        self.uom = uom

    def describe_xml(self):
        elem = OWS.UOM(
            self.uom
        )

        elem.attrib['{%s}reference' % NAMESPACES['ows']] = OGCUNIT[self.uom]

        return elem

    def execute_attribute(self):
        return OGCUNIT[self.uom]


if __name__ == "__main__":
    import doctest
    import os
    from pywps.wpsserver import temp_dir

    with temp_dir() as tmp:
        os.chdir(tmp)
        doctest.testmod()