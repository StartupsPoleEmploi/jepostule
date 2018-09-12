import importlib


def import_object(dotted_path):
    """
    Import an object given its dotted string path.
    """
    names = dotted_path.split('.')
    module = importlib.import_module('.'.join(names[:-1]))
    return getattr(module, names[-1])
