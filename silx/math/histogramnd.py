# coding: utf-8
# /*##########################################################################
# Copyright (C) 2016 European Synchrotron Radiation Facility
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# ############################################################################*/

__authors__ = ["D. Naudet"]
__license__ = "MIT"
__date__ = "15/05/2016"

"""
TOP DOC
"""

import chistogramnd as _chistogramnd
from chistogramnd_lut import histogramnd_get_lut as _histo_get_lut
from chistogramnd_lut import histogramnd_from_lut as _histo_from_lut


def histogramnd(sample,
                bins_rng,
                n_bins,
                weights=None,
                weight_min=None,
                weight_max=None,
                last_bin_closed=False,
                histo=None,
                cumul=None):
    """
    histogramnd(sample, bins_rng, n_bins, weights=None, weight_min=None, weight_max=None, last_bin_closed=False, histo=None, cumul=None)

    Computes the multidimensional histogram of some data.

    :param sample:
        The data to be histogrammed.
        Its shape must be either
        (N,) if it contains one dimensional coordinates,
        or an (N,D) array where the rows are the
        coordinates of points in a D dimensional space.
        The following dtypes are supported : :class:`numpy.float64`,
        :class:`numpy.float32`, :class:`numpy.int32`.
    :type sample: :class:`numpy.array`

    :param bins_rng:
        A (N, 2) array containing the lower and upper
        bin edges along each dimension.
    :type bins_rng: array_like

    :param n_bins:
        The number of bins :
            * a scalar (same number of bins for all dimensions)
            * a D elements array (number of bins for each dimensions)
    :type n_bins: scalar or array_like

    :param weights:
        A N elements numpy array of values associated with
        each sample.
        The values of the *cumul* array
        returned by the function are equal to the sum of
        the weights associated with the samples falling
        into each bin.
        The following dtypes are supported : :class:`numpy.float64`,
        :class:`numpy.float32`, :class:`numpy.int32`.

        .. note:: If None, the weighted histogram returned will be None.
    :type weights: *optional*, :class:`numpy.array`

    :param weight_min:
        Use this parameter to filter out all samples whose
        weights are lower than this value.

        .. note:: This value will be cast to the same type
            as *weights*.
    :type weight_min: *optional*, scalar

    :param weight_max:
        Use this parameter to filter out all samples whose
        weights are higher than this value.

        .. note:: This value will be cast to the same type
            as *weights*.

    :type weight_max: *optional*, scalar

    :param last_bin_closed:
        By default the last bin is half
        open (i.e.: [x,y) ; x included, y
        excluded), like all the other bins.
        Set this parameter to true if you want
        the LAST bin to be closed.
    :type last_bin_closed: *optional*, :class:`python.boolean`

    :param histo:
        Use this parameter if you want to pass your
        own histogram array instead of the one
        created by this function. New values
        will be added to this array. The returned array
        will then be this one (same reference).

        .. warning:: If the histo array was created by a previous
            call to histogramnd then the user is
            responsible for providing the same parameters
            (*n_bins*, *bins_rng*, ...).
    :type histo: *optional*, :class:`numpy.array`

    :param cumul:
        Use this parameter if you want to pass your
        own weighted histogram array instead of
        the created by this function. New
        values will be added to this array. The returned array
        will then be this one (same reference).

        .. warning:: If the cumul array was created by a previous
            call to histogramnd then the user is
            responsible for providing the same parameters
            (*n_bins*, *bins_rng*, ...).
    :type cumul: *optional*, :class:`numpy.array`

    :return: Histogram (bin counts, always returned) and weighted histogram of
        the sample (or *None* if weights is *None*).
    :rtype: *tuple* (:class:`numpy.array`, :class:`numpy.array`) or
        (:class:`numpy.array`, None)
    """

    s_shape = sample.shape

    n_dims = 1 if len(s_shape) == 1 else s_shape[1]

    if weights is not None:
        w_shape = weights.shape

        # making sure the sample and weights sizes are coherent
        # 2 different cases : 2D sample (N,M) and 1D (N)
        if len(w_shape) != 1 or w_shape[0] != s_shape[0]:
                raise ValueError('<weights> must be an array whose length '
                                 'is equal to the number of samples.')

        weights_type = weights.dtype
    else:
        weights_type = None

    # just in case those arent numpy arrays
    # (this allows the user to provide native python lists,
    #   => easier for testing)
    i_bins_rng = bins_rng
    bins_rng = np.array(bins_rng)
    err_bins_rng = False

    if n_dims == 1:
        if bins_rng.shape == (2,):
            pass
        elif bins_rng.shape == (1, 2):
            bins_rng.shape = -1
        else:
            err_bins_rng = True
    elif n_dims != 1 and bins_rng.shape != (n_dims, 2):
        err_bins_rng = True

    if err_bins_rng:
        raise ValueError('<bins_rng> error : expected {n_dims} sets of '
                         'lower and upper bin edges, '
                         'got the following instead : {bins_rng}. '
                         '(provided <sample> contains '
                         '{n_dims}D values)'
                         ''.format(bins_rng=i_bins_rng,
                                   n_dims=n_dims))

    # checking n_bins size
    n_bins = np.array(n_bins, ndmin=1)
    if len(n_bins) == 1:
        n_bins = np.tile(n_bins, n_dims)
    elif n_bins.shape != (n_dims,):
        raise ValueError('n_bins must be either a scalar (same number '
                         'of bins for all dimensions) or '
                         'an array (number of bins for each '
                         'dimension).')

    # checking if None is in n_bins, otherwise a rather cryptic
    #   exception is thrown when calling np.zeros
    # also testing for negative/null values
    if np.any(np.equal(n_bins, None)) or np.any(n_bins <= 0):
        raise ValueError('<n_bins> : only positive values allowed.')

    output_shape = tuple(n_bins)

    # checking the histo array, if provided
    if histo is None:
        histo = np.zeros(output_shape, dtype=np.uint32)
    else:
        if histo.shape != output_shape:
            raise ValueError('Provided <histo> array doesn\'t have '
                             'a shape compatible with <n_bins> '
                             ': should be {0} instead of {1}.'
                             ''.format(output_shape, histo.shape))
        if histo.dtype != np.uint32:
            raise ValueError('Provided <histo> array doesn\'t have '
                             'the expected type '
                             ': should be {0} instead of {1}.'
                             ''.format(np.uint32, histo.dtype))

    # checking the cumul array, if provided
    if weights_type is None:
        cumul = None
    elif cumul is None:
        cumul = np.zeros(output_shape, dtype=np.double)
    else:
        if cumul.shape != output_shape:
            raise ValueError('Provided <cumul> array doesn\'t have '
                             'a shape compatible with <n_bins> '
                             ': should be {0} instead of {1}.'
                             ''.format(output_shape, cumul.shape))
        if cumul.dtype != np.float64 and cumul.dtype != np.float32:
            raise ValueError('Provided <cumul> array doesn\'t have '
                             'the expected type '
                             ': should be {0} or {1} instead of {2}.'
                             ''.format(np.double, np.float32, cumul.dtype))

    option_flags = 0

    if weight_min is not None:
        option_flags |= histogramnd_c.HISTO_WEIGHT_MIN
    else:
        weight_min = 0

    if weight_max is not None:
        option_flags |= histogramnd_c.HISTO_WEIGHT_MAX
    else:
        weight_max = 0

    if last_bin_closed is not None and last_bin_closed:
        option_flags |= histogramnd_c.HISTO_LAST_BIN_CLOSED

    sample_type = sample.dtype

    n_elem = sample.size // n_dims

    # wanted to store the functions in a dict (with the supported types
    # as keys, but I couldn't find a way to make it work with cdef
    # functions. so I have to explicitly list them all...

    def raise_unsupported_type():
        raise TypeError('Case not supported - sample:{0} '
                        'and weights:{1}.'
                        ''.format(sample_type, weights_type))

    sample_c = np.ascontiguousarray(sample.reshape((sample.size,)))

    weights_c = (np.ascontiguousarray(weights.reshape((weights.size,)))
                 if weights is not None else None)

    bins_rng_c = np.ascontiguousarray(bins_rng.reshape((bins_rng.size,)),
                                      dtype=sample_type)

    n_bins_c = np.ascontiguousarray(n_bins.reshape((n_bins.size,)),
                                    dtype=np.int32)

    histo_c = np.ascontiguousarray(histo.reshape((histo.size,)))

    if cumul is not None:
        cumul_c = np.ascontiguousarray(cumul.reshape((cumul.size,)))
    else:
        cumul_c = None

    rc = 0

    # this aint pretty...
    if cumul is None or cumul.dtype == np.double:

        if sample_type == np.float64:

            if weights_type == np.float64 or weights_type is None:

                rc = _histogramnd_double_double_double(sample_c,
                                                       weights_c,
                                                       n_dims,
                                                       n_elem,
                                                       bins_rng_c,
                                                       n_bins_c,
                                                       histo_c,
                                                       cumul_c,
                                                       option_flags,
                                                       weight_min=weight_min,
                                                       weight_max=weight_max)

            elif weights_type == np.float32:

                rc = _histogramnd_double_float_double(sample_c,
                                                      weights_c,
                                                      n_dims,
                                                      n_elem,
                                                      bins_rng_c,
                                                      n_bins_c,
                                                      histo_c,
                                                      cumul_c,
                                                      option_flags,
                                                      weight_min=weight_min,
                                                      weight_max=weight_max)

            elif weights_type == np.int32:

                rc = _histogramnd_double_int32_t_double(sample_c,
                                                        weights_c,
                                                        n_dims,
                                                        n_elem,
                                                        bins_rng_c,
                                                        n_bins_c,
                                                        histo_c,
                                                        cumul_c,
                                                        option_flags,
                                                        weight_min=weight_min,
                                                        weight_max=weight_max)

            else:
                raise_unsupported_type()

        # endif sample_type == np.float64
        elif sample_type == np.float32:

            if weights_type == np.float64 or weights_type is None:

                rc = _histogramnd_float_double_double(sample_c,
                                                      weights_c,
                                                      n_dims,
                                                      n_elem,
                                                      bins_rng_c,
                                                      n_bins_c,
                                                      histo_c,
                                                      cumul_c,
                                                      option_flags,
                                                      weight_min=weight_min,
                                                      weight_max=weight_max)

            elif weights_type == np.float32:

                rc = _histogramnd_float_float_double(sample_c,
                                                     weights_c,
                                                     n_dims,
                                                     n_elem,
                                                     bins_rng_c,
                                                     n_bins_c,
                                                     histo_c,
                                                     cumul_c,
                                                     option_flags,
                                                     weight_min=weight_min,
                                                     weight_max=weight_max)

            elif weights_type == np.int32:

                rc = _histogramnd_float_int32_t_double(sample_c,
                                                       weights_c,
                                                       n_dims,
                                                       n_elem,
                                                       bins_rng_c,
                                                       n_bins_c,
                                                       histo_c,
                                                       cumul_c,
                                                       option_flags,
                                                       weight_min=weight_min,
                                                       weight_max=weight_max)

            else:
                raise_unsupported_type()

        # endif sample_type == np.float32
        elif sample_type == np.int32:

            if weights_type == np.float64 or weights_type is None:

                rc = _histogramnd_int32_t_double_double(sample_c,
                                                        weights_c,
                                                        n_dims,
                                                        n_elem,
                                                        bins_rng_c,
                                                        n_bins_c,
                                                        histo_c,
                                                        cumul_c,
                                                        option_flags,
                                                        weight_min=weight_min,
                                                        weight_max=weight_max)

            elif weights_type == np.float32:

                rc = _histogramnd_int32_t_float_double(sample_c,
                                                       weights_c,
                                                       n_dims,
                                                       n_elem,
                                                       bins_rng_c,
                                                       n_bins_c,
                                                       histo_c,
                                                       cumul_c,
                                                       option_flags,
                                                       weight_min=weight_min,
                                                       weight_max=weight_max)

            elif weights_type == np.int32:

                rc = _histogramnd_int32_t_int32_t_double(sample_c,
                                                         weights_c,
                                                         n_dims,
                                                         n_elem,
                                                         bins_rng_c,
                                                         n_bins_c,
                                                         histo_c,
                                                         cumul_c,
                                                         option_flags,
                                                         weight_min=weight_min,
                                                         weight_max=weight_max)

            else:
                raise_unsupported_type()

        # endif sample_type == np.int32:
        else:
            raise_unsupported_type()

    # endif cumul is None or cumul.dtype == np.double:
    elif cumul.dtype == np.float32:

        if sample_type == np.float64:

            if weights_type == np.float64 or weights_type is None:

                rc = _histogramnd_double_double_float(sample_c,
                                                      weights_c,
                                                      n_dims,
                                                      n_elem,
                                                      bins_rng_c,
                                                      n_bins_c,
                                                      histo_c,
                                                      cumul_c,
                                                      option_flags,
                                                      weight_min=weight_min,
                                                      weight_max=weight_max)

            elif weights_type == np.float32:

                rc = _histogramnd_double_float_float(sample_c,
                                                     weights_c,
                                                     n_dims,
                                                     n_elem,
                                                     bins_rng_c,
                                                     n_bins_c,
                                                     histo_c,
                                                     cumul_c,
                                                     option_flags,
                                                     weight_min=weight_min,
                                                     weight_max=weight_max)

            elif weights_type == np.int32:

                rc = _histogramnd_double_int32_t_float(sample_c,
                                                       weights_c,
                                                       n_dims,
                                                       n_elem,
                                                       bins_rng_c,
                                                       n_bins_c,
                                                       histo_c,
                                                       cumul_c,
                                                       option_flags,
                                                       weight_min=weight_min,
                                                       weight_max=weight_max)

            else:
                raise_unsupported_type()

        # endif sample_type == np.float64
        elif sample_type == np.float32:

            if weights_type == np.float64 or weights_type is None:

                rc = _histogramnd_float_double_float(sample_c,
                                                     weights_c,
                                                     n_dims,
                                                     n_elem,
                                                     bins_rng_c,
                                                     n_bins_c,
                                                     histo_c,
                                                     cumul_c,
                                                     option_flags,
                                                     weight_min=weight_min,
                                                     weight_max=weight_max)

            elif weights_type == np.float32:

                rc = _histogramnd_float_float_float(sample_c,
                                                    weights_c,
                                                    n_dims,
                                                    n_elem,
                                                    bins_rng_c,
                                                    n_bins_c,
                                                    histo_c,
                                                    cumul_c,
                                                    option_flags,
                                                    weight_min=weight_min,
                                                    weight_max=weight_max)

            elif weights_type == np.int32:

                rc = _histogramnd_float_int32_t_float(sample_c,
                                                      weights_c,
                                                      n_dims,
                                                      n_elem,
                                                      bins_rng_c,
                                                      n_bins_c,
                                                      histo_c,
                                                      cumul_c,
                                                      option_flags,
                                                      weight_min=weight_min,
                                                      weight_max=weight_max)

            else:
                raise_unsupported_type()

        # endif sample_type == np.float32
        elif sample_type == np.int32:

            if weights_type == np.float64 or weights_type is None:

                rc = _histogramnd_int32_t_double_float(sample_c,
                                                       weights_c,
                                                       n_dims,
                                                       n_elem,
                                                       bins_rng_c,
                                                       n_bins_c,
                                                       histo_c,
                                                       cumul_c,
                                                       option_flags,
                                                       weight_min=weight_min,
                                                       weight_max=weight_max)

            elif weights_type == np.float32:

                rc = _histogramnd_int32_t_float_float(sample_c,
                                                      weights_c,
                                                      n_dims,
                                                      n_elem,
                                                      bins_rng_c,
                                                      n_bins_c,
                                                      histo_c,
                                                      cumul_c,
                                                      option_flags,
                                                      weight_min=weight_min,
                                                      weight_max=weight_max)

            elif weights_type == np.int32:

                rc = _histogramnd_int32_t_int32_t_float(sample_c,
                                                        weights_c,
                                                        n_dims,
                                                        n_elem,
                                                        bins_rng_c,
                                                        n_bins_c,
                                                        histo_c,
                                                        cumul_c,
                                                        option_flags,
                                                        weight_min=weight_min,
                                                        weight_max=weight_max)

            else:
                raise_unsupported_type()

        # endif sample_type == np.int32:
        else:
            raise_unsupported_type()

    # end elseif cumul.dtype == np.float32:
    else:
        # this isnt supposed to happen since cumul type was checked earlier
        raise_unsupported_type()

    if rc != histogramnd_c.HISTO_OK:
        if rc == histogramnd_c.HISTO_ERR_ALLOC:
            raise MemoryError('histogramnd failed to allocate memory.')
        else:
            raise Exception('histogramnd returned an error : {0}'
                            ''.format(rc))

    return histo, cumul


class HistogramLut(object):
    """
    ``HistogramLut(sample, bins_rng, n_bins, last_bin_closed=True)``
    The HistogramLut class allows you to bin data onto a regular grid.
    The use of HistogramLut is interesting when several sets of data that
    share the same coordinates (*sample*) have to be mapped onto the same grid.

    .. seealso::
        `silx.math.histogramnd`

    :param sample:
        The coordinates of the data to be histogrammed.
        Its shape must be either (N,) if it contains one dimensional
        coordinates, or an (N, D) array where the rows are the
        coordinates of points in a D dimensional space.
        The following dtypes are supported : :class:`numpy.float64`,
        :class:`numpy.float32`, :class:`numpy.int32`.
    :type sample: :class:`numpy.array`

    :param bins_rng:
        A (N, 2) array containing the lower and upper
        bin edges along each dimension.
    :type bins_rng: array_like

    :param n_bins:
        The number of bins :
            * a scalar (same number of bins for all dimensions)
            * a D elements array (number of bins for each dimensions)
    :type n_bins: scalar or array_like

    :param dtype: data type of the weighted histogram. If None, the data type
        will be the same as the first weights array provided (on first call of
        the instance).
    :type dtype: `numpy.dtype`

    :param last_bin_closed:
        By default the last bin is half
        open (i.e.: [x,y) ; x included, y
        excluded), like all the other bins.
        Set this parameter to true if you want
        the LAST bin to be closed.
    :type last_bin_closed: *optional*, :class:`python.boolean`
    """
    def __init__(self,
                 sample,
                 bins_rng,
                 n_bins,
                 last_bin_closed=True,
                 dtype=None):
        """
        TTTTT
        """
        lut, histo = _histo_get_lut(sample,
                                    bins_rng,
                                    n_bins,
                                    last_bin_closed=last_bin_closed)
        self.__n_bins = n_bins
        self.__bins_rng = bins_rng
        self.__lut = lut
        self.__histo = histo
        self.__dtype = dtype
        self.reset()
        
    def reset(self):
        self.__weighted_histo = None
        self.__n_histo = 0

    def __get_weighted_histo(self):
        if self.__n_histo > 0:
            return self.__weighted_histo.copy()
        else:
            return None

    def __get_histo(self):
        return self.__histo.copy()
#        if self.__n_histo > 0:
#            return self.__histo.copy() * self.__n_histo
#        else:
#            return None

    def __get_dtype(self):
        return self.__dtype

    def __get_bins_rng(self):
        return self.__bins_rng

    def __get_n_bins(self):
        return self.__n_bins

    def __get_n_histo(self):
        return self.__n_histo

    def accumulate(self,
                   weights,
                   weight_min=None,
                   weight_max=None):

        if self.__dtype is None:
            self.__dtype = weights.dtype

        w_histo = _histo_from_lut(weights,
                                  self.__lut,
                                  shape=self.__histo.shape,
                                  weighted_histo=self.__weighted_histo,
                                  dtype=self.__dtype,
                                  weight_min=weight_min,
                                  weight_max=weight_max)
        self.__weighted_histo = w_histo
        self.__n_histo += 1

    def apply(self,
              weights,
              weighted_histo=None,
              weight_min=None,
              weight_max=None):

        if weighted_histo is None:
            if self.__dtype is None:
                dtype = weights.dtype
            else:
                dtype = self.__dtype

        w_histo = _histog_from_lut(weights,
                                   self.__lut,
                                   shape=self.__histo.shape,
                                   weighted_histo=weighted_histo,
                                   dtype=dtype,
                                   weight_min=weight_min,
                                   weight_max=weight_max)
        return self.__histo, w_histo

    histo = property(__get_histo)
    """ Test doc property """
    weighted_histo = property(__get_weighted_histo)
    dtype = property(__get_dtype)
    bins_rng = property(__get_bins_rng)
    n_bins = property(__get_n_bins)
    n_histo = property(__get_n_histo)
