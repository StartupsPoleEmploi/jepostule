import pickle


def dumps(*args, **kwargs):
    """
    Serialize data to a binary format.

    Return:
        value (bytes)
    """
    try:
        return pickle.dumps({
            'args': args,
            'kwargs': kwargs,
        })
    except pickle.PicklingError:
        raise EncodeError


def loads(value):
    """
    Deserialize data from a binary format.

    Args:
        value (bytes)

    Return:
        args (list)
        kwargs (dict)
    """
    try:
        data = pickle.loads(value)
    except pickle.UnpicklingError:
        raise DecodeError
    return data['args'], data['kwargs']


class EncodeError(Exception):
    pass

class DecodeError(Exception):
    pass
