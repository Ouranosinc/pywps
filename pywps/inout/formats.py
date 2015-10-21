# List of known complex data formats
# you can use any other, but thise are widly known and supported by polular
# software packages
# based on Web Processing Service Best Practices Discussion Paper, OGC 12-029
# http://opengeospatial.org/standards/wps

"""List of known mimetypes
"""

from lxml.builder import ElementMaker
from collections import namedtuple
import mimetypes

_FORMAT = namedtuple('FormatDefintion', 'mime_type,'
                     'extension, schema')
_FORMATS = namedtuple('FORMATS', 'GEOJSON, JSON, SHP, GML, GEOTIFF, WCS,'
                                 'WCS100, WCS110, WCS20, WFS, WFS100,'
                                 'WFS110, WFS20, WMS, WMS130, WMS110,'
                                 'WMS100')
FORMATS = _FORMATS(
    _FORMAT('application/vnd.geo+json', '.geojson',  None),
    _FORMAT('application/json', '.json',  None),
    _FORMAT('application/x-zipped-shp', '.zip',  None),
    _FORMAT('application/gml+xml', '.gml', None),
    _FORMAT('image/tiff; subtype=geotiff', '.tiff', None),
    _FORMAT('application/xogc-wcs', '.xml', None),
    _FORMAT('application/x-ogc-wcs; version=1.0.0', '.xml', None),
    _FORMAT('application/x-ogc-wcs; version=1.1.0', '.xml', None),
    _FORMAT('application/x-ogc-wcs; version=2.0', '.xml', None),
    _FORMAT('application/x-ogc-wfs', '.xml', None),
    _FORMAT('application/x-ogc-wfs; version=1.0.0', '.xml', None),
    _FORMAT('application/x-ogc-wfs; version=1.1.0', '.xml', None),
    _FORMAT('application/x-ogc-wfs; version=2.0', '.xml', None),
    _FORMAT('application/x-ogc-wms', '.xml', None),
    _FORMAT('application/x-ogc-wms; version=1.3.0', '.xml', None),
    _FORMAT('application/x-ogc-wms; version=1.1.0', '.xml', None),
    _FORMAT('application/x-ogc-wms; version=1.0.0', '.xml', None)
)

def _get_mimetypes():
    """Add FORMATS to system wide mimetypes
    """
    mimetypes.init()
    for pywps_format in FORMATS:
        mimetypes.add_type(pywps_format.mime_type, pywps_format.extension, True)
_get_mimetypes()


class Format(object):
    """Input/output format specification
    """
    def __init__(self, mime_type,
                 schema=None, encoding=None, validate=None, extension=None):
        """Constructor

        :param mime_type: mimetype definition
        :schema: xml schema definition
        :encoding: base64 or not
        :validate: function, which will perform validation. e.g.
        pywps.validator.complexvalidator.validategml
        """

        self._mime_type = None
        self._encoding = None
        self._schema = None

        self.mime_type = mime_type
        self.encoding = encoding
        self.schema = schema
        self.validate = validate
        self.extension = extension


    @property
    def mime_type(self):
        """Get format mime type
        :rtype: String
        """

        return self._mime_type

    @mime_type.setter
    def mime_type(self, mime_type):
        """Set format mime type
        """

        self._mime_type = mime_type

    @property
    def encoding(self):
        """Get format encoding
        :rtype: String
        """

        if self._encoding:
            return self._encoding
        else:
            return ''

    @encoding.setter
    def encoding(self, encoding):
        """Set format encoding
        """

        self._encoding = encoding

    @property
    def schema(self):
        """Get format schema
        :rtype: String
        """
        if self._schema:
            return self._schema
        else:
            return ''

    @schema.setter
    def schema(self, schema):
        """Set format schema
        """
        self._schema = schema


    def same_as(self, frmt):
        """Check input frmt, if it seems to be the same as self
        """
        return frmt.mime_type == self.mime_type and\
               frmt.encoding == self.encoding and\
               frmt.schema == self.schema

    def describe_xml(self):
        """Return describe process response element
        """

        elmar = ElementMaker()
        doc = elmar.Format(
            elmar.MimeType(self.mime_type)
        )


        if self.encoding:
            doc.append(elmar.Encoding(self.encoding))

        if self.schema:
            doc.append(elmar.Schema(self.schema))

        return doc

def get_format(frmt, validator=None):
    """Return Format instance based on given pywps.inout.FORMATS keyword
    """

    outfrmt = None

    if frmt in FORMATS._asdict():
        formatdef = FORMATS._asdict()[frmt]
        outfrmt = Format(**formatdef._asdict())
        outfrmt.validate=validator
        return outfrmt
    else:
        return Format('None', validate=validator)