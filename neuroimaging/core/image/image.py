"""The image module provides basic functions for working with images in nipy.
Functions are provided to load, save and create image objects, along with
iterators to easily slice through volumes.

    load : load an image from a file

    save : save an image to a file

    fromarray : create an image from a numpy array

Examples
--------
See documentation for load and save functions for 'working' examples.

"""
import numpy as np

from neuroimaging.core.reference.coordinate_map import CoordinateMap
from neuroimaging.core.reference.mapping import Affine
from neuroimaging.io.pyniftiio import PyNiftiIO, orientation_to_names


__docformat__ = 'restructuredtext'
__all__ = ['load', 'save', 'fromarray']

class Image(object):
    """
    The `Image` class provides the core object type used in nipy. An `Image`
    represents a volumetric brain image and provides means for manipulating
    the image data.  Most functions in the image module operate on `Image`
    objects.

    Notes
    -----
    Images should be created through the module functions load and fromarray.

    Examples
    --------

    >>> from neuroimaging.core.image import image
    >>> from neuroimaging.testing import anatfile
    >>> img = image.load(anatfile)

    >>> import numpy as np
    >>> img = image.fromarray(np.zeros((21, 64, 64), dtype='int16'),
    ...                       ['zspace', 'yspace', 'xspace'])

    """

    def __init__(self, data, coordmap):
        """Create an `Image` object from array and ``CoordinateMap`` object.
        
        Images should be created through the module functions load and
        fromarray.

        Parameters
        ----------
        data : A numpy.ndarray
        coordmap : A `CoordinateMap` Object
        
        See Also
        --------
        load : load `Image` from a file
        save : save `Image` to a file
        fromarray : create an `Image` from a numpy array

        """

        if data is None or coordmap is None:
            raise ValueError, 'expecting an array and CoordinateMap instance'

        # self._data is an array-like object.  It must implement a subset of
        # array methods  (Need to specify these, for now implied in pyniftio)
        self._data = data
        self._coordmap = coordmap

    def _getshape(self):
        return self._data.shape
    shape = property(_getshape, doc="Shape of data array")

    def _getndim(self):
        return self._data.ndim
    ndim = property(_getndim, doc="Number of data dimensions")

    def _getcoordmap(self):
        return self._coordmap
    coordmap = property(_getcoordmap,
                    doc="Coordinate mapping from input coords to output coords")

    def _getaffine(self):
        if hasattr(self.coordmap, "affine"):
            return self.coordmap.affine
        raise AttributeError, 'Nonlinear transform does not have an affine.'
    affine = property(_getaffine, doc="Affine transformation is one exists")

    def _getheader(self):
        # data loaded from a file should have a header
        if hasattr(self._data, 'header'):
            return self._data.header
        raise AttributeError, 'Image created from arrays do not have headers.'
    def _setheader(self, header):
        if hasattr(self._data, 'header'):
            self._data.header = header
        else:
            raise AttributeError, \
                  'Image created from arrays do not have headers.'
    header = property(_getheader, _setheader,
                      doc="Image header, if the image has one.")

    def __getitem__(self, index):
        """Slicing an image returns a new image."""
        data = self._data[index]
        coordmap = self.coordmap[index]
        # BUG: If it's a zero-dimension array we should return a numpy scalar
        # like np.int32(data[index])
        # Need to figure out elegant way to handle this
        return Image(data, coordmap)

    def __setitem__(self, index, value):
        """Setting values of an image, set values in the data array."""
        self._data[index] = value

    def __array__(self):
        """Return data as a numpy array."""
        return np.asarray(self._data)

def _open(source, coordmap=None, mode="r", dtype=None):
    """Create an `Image` from the given filename

    Parameters
    ----------
    source : filename or a numpy array
    coordmap : `reference.coordinate_map.CoordinateMap`
        The coordinate map for the file
    mode : ``string``
        The mode ot open the file in ('r', 'w', etc)

    Returns
    -------
    image : A new `Image` object created from the filename.

    """

    try:
        if hasattr(source, 'header'):
            hdr = source.header
        else:
            hdr = {}
        ioimg = PyNiftiIO(source, mode, dtype=dtype, header=hdr)
        if coordmap is None:
            coordmap = _coordmap_from_affine(ioimg.affine, ioimg.orientation,
                                    ioimg.shape)
        # Build nipy image from array-like object and coordinate map
        img = Image(ioimg, coordmap)
        return img
    except IOError:
        raise IOError, 'Unable to create image from source %s' % str(source)
        
def load(filename, mode='r'):
    """Load an image from the given filename.

    Load an image from the file specified by ``filename``.

    Parameters
    ----------
    filename : string
        Should resolve to a complete filename path.
    mode : Either 'r' or 'r+'

    Returns
    -------
    image : An `Image` object
        If successful, a new `Image` object is returned.

    See Also
    --------
    save_image : function for saving images
    fromarray : function for creating images from numpy arrays

    Examples
    --------

    >>> from neuroimaging.core.api import load_image
    >>> from neuroimaging.testing import anatfile
    >>> img = load_image(anatfile)
    >>> img.shape
    (25, 35, 25)

    """

    if mode not in ['r', 'r+']:
        raise ValueError, 'image opening mode must be either "r" or "r+"'
    return _open(filename, mode=mode)

def save(img, filename, dtype=None):
    """Write the image to a file.

    Parameters
    ----------
    img : An `Image` object
    filename : string
        Should be a valid filename.

    Returns
    -------
    image : An `Image` object

    See Also
    --------
    load_image : function for loading images
    fromarray : function for creating images from numpy arrays

    Examples
    --------

    >>> import numpy as np
    >>> from tempfile import NamedTemporaryFile
    >>> from neuroimaging.core.api import save_image, fromarray
    >>> data = np.zeros((91,109,91), dtype=np.uint8)
    >>> img = fromarray(data)
    >>> tmpfile = NamedTemporaryFile(suffix='.nii.gz')
    >>> saved_img = save_image(img, tmpfile.name)
    >>> saved_img.shape
    (91, 109, 91)

    Notes
    -----
    Filetype is determined by the file extension in 'filename'.  Currently the
    following filetypes are supported:
        Nifti single file : ['.nii', '.nii.gz']
        Nifti file pair : ['.hdr', '.hdr.gz']
        Analyze file pair : ['.img', 'img.gz']
        
    """

    # Pass the image object to the low-level IO class so it can handle
    # any data scaling.
    outimage = _open(img, coordmap=img.coordmap, mode='w', dtype=dtype)
    # At this point _data is a file-io object (like PyNiftiIO).
    # _data.save delegates the save to pynifti.
    
    # FIXME:  HACK? Is this the correct way to handle saving fmri images?
    if img.affine.shape == (5, 5):
        # pull spatial transforms out of 5x5 fmri affine
        affine = img.affine[1:, 1:]
    else:
        affine = img.affine
    outimage._data.save(affine, filename)
    return outimage
    
def fromarray(data, names=['zspace', 'yspace', 'xspace'], coordmap=None):
    """Create an image from a numpy array.

    Parameters
    ----------
    data : numpy array
        A numpy array of three dimensions.
    names : a list of axis names
    coordmap : A `CoordinateMap`
        If not specified, a uniform coordinate map is created.

    Returns
    -------
    image : An `Image` object

    See Also
    --------
    load : function for loading images
    save : function for saving images

    """

    ndim = len(data.shape)
    if not coordmap:
        coordmap = CoordinateMap.from_start_step(names,
                                            (0,)*ndim,
                                            (1,)*ndim,
                                            data.shape)

    return Image(data, coordmap)

def merge_images(filename, images, cls=Image, clobber=False,
                 axis='time'):
    """
    Create a new file based image by combining a series of images together.

    Parameters
    ----------
    filename : ``string``
        The filename to write the new image as
    images : [`Image`]
        The list of images to be merged
    cls : ``class``
        The class of image to create
    clobber : ``bool``
        Overwrite the file if it already exists
    axis : ``string``
        Name of the concatenated axis.
        
    Returns
    -------
    ``cls``
    
    """
    
    n = len(images)
    im0 = images[0]
    coordmap = im0.coordmap.replicate(n, axis)
    data = np.empty(shape=coordmap.shape)
    for i, image in enumerate(images):
        data[i] = np.asarray(image)[:]
    return Image(data, coordmap)

def _coordmap_from_affine(affine, orientation, shape):
    """Generate a CoordinateMap from an affine transform.

    This is a convenience function to create a CoordinateMap from image
    attributes.  It uses the orientation field from pynifti IO to map
    to the nipy *names*, prepending *time* or *vector* depending on
    dimension.

    FIXME: This is an internal function and should be revisited when
    the CoordinateMap is refactored.
    
    """

    names = []
    for ornt in orientation:
        names.append(orientation_to_names.get(ornt))
    names = names[::-1]
    if len(shape) == 4:
        names = ['time'] + names
    elif len(shape) == 5:
        names = ['vector', 'time'] + names
    affobj = Affine(affine)
    coordmap = CoordinateMap.from_affine(affobj, names, shape)
    return coordmap
