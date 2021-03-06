import pytest
with pytest.suppress(ImportError):
    import numpy as np

    simple_dtype = np.dtype({'names': ['x', 'y', 'z'],
                             'formats': ['?', 'u4', 'f4'],
                             'offsets': [0, 4, 8]})
    packed_dtype = np.dtype([('x', '?'), ('y', 'u4'), ('z', 'f4')])


def assert_equal(actual, expected_data, expected_dtype):
    np.testing.assert_equal(actual, np.array(expected_data, dtype=expected_dtype))


@pytest.requires_numpy
def test_format_descriptors():
    from pybind11_tests import get_format_unbound, print_format_descriptors

    with pytest.raises(RuntimeError) as excinfo:
        get_format_unbound()
    assert 'unsupported buffer format' in str(excinfo.value)

    assert print_format_descriptors() == [
        "T{=?:x:3x=I:y:=f:z:}",
        "T{=?:x:=I:y:=f:z:}",
        "T{=T{=?:x:3x=I:y:=f:z:}:a:=T{=?:x:=I:y:=f:z:}:b:}",
        "T{=?:x:3x=I:y:=f:z:12x}",
        "T{8x=T{=?:x:3x=I:y:=f:z:12x}:a:8x}",
        "T{=3s:a:=3s:b:}"
    ]


@pytest.requires_numpy
def test_dtype():
    from pybind11_tests import print_dtypes, test_dtype_ctors, test_dtype_methods

    assert print_dtypes() == [
        "{'names':['x','y','z'], 'formats':['?','<u4','<f4'], 'offsets':[0,4,8], 'itemsize':12}",
        "[('x', '?'), ('y', '<u4'), ('z', '<f4')]",
        "[('a', {'names':['x','y','z'], 'formats':['?','<u4','<f4'], 'offsets':[0,4,8], 'itemsize':12}), ('b', [('x', '?'), ('y', '<u4'), ('z', '<f4')])]",
        "{'names':['x','y','z'], 'formats':['?','<u4','<f4'], 'offsets':[0,4,8], 'itemsize':24}",
        "{'names':['a'], 'formats':[{'names':['x','y','z'], 'formats':['?','<u4','<f4'], 'offsets':[0,4,8], 'itemsize':24}], 'offsets':[8], 'itemsize':40}",
        "[('a', 'S3'), ('b', 'S3')]"
    ]

    d1 = np.dtype({'names': ['a', 'b'], 'formats': ['int32', 'float64'],
                   'offsets': [1, 10], 'itemsize': 20})
    d2 = np.dtype([('a', 'i4'), ('b', 'f4')])
    assert test_dtype_ctors() == [np.dtype('int32'), np.dtype('float64'),
                                  np.dtype('bool'), d1, d1, np.dtype('uint32'), d2]

    assert test_dtype_methods() == [np.dtype('int32'), simple_dtype, False, True,
                                    np.dtype('int32').itemsize, simple_dtype.itemsize]


@pytest.requires_numpy
def test_recarray():
    from pybind11_tests import (create_rec_simple, create_rec_packed, create_rec_nested,
                                print_rec_simple, print_rec_packed, print_rec_nested,
                                create_rec_partial, create_rec_partial_nested)

    elements = [(False, 0, 0.0), (True, 1, 1.5), (False, 2, 3.0)]

    for func, dtype in [(create_rec_simple, simple_dtype), (create_rec_packed, packed_dtype)]:
        arr = func(0)
        assert arr.dtype == dtype
        assert_equal(arr, [], simple_dtype)
        assert_equal(arr, [], packed_dtype)

        arr = func(3)
        assert arr.dtype == dtype
        assert_equal(arr, elements, simple_dtype)
        assert_equal(arr, elements, packed_dtype)

        if dtype == simple_dtype:
            assert print_rec_simple(arr) == [
                "s:0,0,0",
                "s:1,1,1.5",
                "s:0,2,3"
            ]
        else:
            assert print_rec_packed(arr) == [
                "p:0,0,0",
                "p:1,1,1.5",
                "p:0,2,3"
            ]

    nested_dtype = np.dtype([('a', simple_dtype), ('b', packed_dtype)])

    arr = create_rec_nested(0)
    assert arr.dtype == nested_dtype
    assert_equal(arr, [], nested_dtype)

    arr = create_rec_nested(3)
    assert arr.dtype == nested_dtype
    assert_equal(arr, [((False, 0, 0.0), (True, 1, 1.5)),
                       ((True, 1, 1.5), (False, 2, 3.0)),
                       ((False, 2, 3.0), (True, 3, 4.5))], nested_dtype)
    assert print_rec_nested(arr) == [
        "n:a=s:0,0,0;b=p:1,1,1.5",
        "n:a=s:1,1,1.5;b=p:0,2,3",
        "n:a=s:0,2,3;b=p:1,3,4.5"
    ]

    arr = create_rec_partial(3)
    assert str(arr.dtype) == "{'names':['x','y','z'], 'formats':['?','<u4','<f4'], 'offsets':[0,4,8], 'itemsize':24}"
    partial_dtype = arr.dtype
    assert '' not in arr.dtype.fields
    assert partial_dtype.itemsize > simple_dtype.itemsize
    assert_equal(arr, elements, simple_dtype)
    assert_equal(arr, elements, packed_dtype)

    arr = create_rec_partial_nested(3)
    assert str(arr.dtype) == "{'names':['a'], 'formats':[{'names':['x','y','z'], 'formats':['?','<u4','<f4'], 'offsets':[0,4,8], 'itemsize':24}], 'offsets':[8], 'itemsize':40}"
    assert '' not in arr.dtype.fields
    assert '' not in arr.dtype.fields['a'][0].fields
    assert arr.dtype.itemsize > partial_dtype.itemsize
    np.testing.assert_equal(arr['a'], create_rec_partial(3))


@pytest.requires_numpy
def test_array_constructors():
    from pybind11_tests import test_array_ctors

    data = np.arange(1, 7, dtype='int32')
    for i in range(8):
        np.testing.assert_array_equal(test_array_ctors(10 + i), data.reshape((3, 2)))
        np.testing.assert_array_equal(test_array_ctors(20 + i), data.reshape((3, 2)))
    for i in range(5):
        np.testing.assert_array_equal(test_array_ctors(30 + i), data)
        np.testing.assert_array_equal(test_array_ctors(40 + i), data)


@pytest.requires_numpy
def test_string_array():
    from pybind11_tests import create_string_array, print_string_array

    arr = create_string_array(True)
    assert str(arr.dtype) == "[('a', 'S3'), ('b', 'S3')]"
    assert print_string_array(arr) == [
        "a='',b=''",
        "a='a',b='a'",
        "a='ab',b='ab'",
        "a='abc',b='abc'"
    ]
    dtype = arr.dtype
    assert arr['a'].tolist() == [b'', b'a', b'ab', b'abc']
    assert arr['b'].tolist() == [b'', b'a', b'ab', b'abc']
    arr = create_string_array(False)
    assert dtype == arr.dtype


@pytest.requires_numpy
def test_signature(doc):
    from pybind11_tests import create_rec_nested

    assert doc(create_rec_nested) == "create_rec_nested(arg0: int) -> numpy.ndarray[NestedStruct]"
