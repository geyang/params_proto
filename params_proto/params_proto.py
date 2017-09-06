import argparse
import inspect
import re
import sys
from typing import TypeVar

from munch import DefaultMunch


def is_hidden(k: str) -> bool:
    """return True is method is hidden"""
    return bool(re.match("^_.*$", k))


T = TypeVar('T')


class ParamsProto:
    """Parameter Prototype Class, has toDict method and __proto__ attribute for the original namespace object."""
    __proto__ = None

    # noinspection PyPep8Naming
    @staticmethod
    def toDict() -> dict:
        pass
        # raise NotImplementedError('should be overwritten')


# noinspection PyTypeChecker
def cli_parse(proto: T) -> T:
    """parser command line options, and repackage into a typed object.
    :type proto: T
    """
    parser = argparse.ArgumentParser(description=T.__doc__)
    for k, v in proto.__dict__.items():
        if is_hidden(k):
            continue
        k_normalized = k.replace('_', '-')
        if sys.version_info >= (3, 6):
            default = v
            help_str = proto.__annotations__[k]
        else:  # use array as proto attribute value for python <= 3.5
            assert len(v) >= 1, "for python version <= 3.5, use a tuple to define the parameter prototype."
            default, *_ = v
            if len(_) > 0:
                help_str = _[0]
            else:
                help_str = None
        data_type = type(default)
        parser.add_argument('--{k}'.format(k=k_normalized), default=default, type=data_type, help=help_str)

    if sys.version_info <= (3, 6):
        params = DefaultMunch(None, {k: v[0] for k, v in vars(proto).items() if not is_hidden(k)})
    else:
        params = DefaultMunch(None, {k: v for k, v in vars(proto).items() if not is_hidden(k)})

    params.update(vars(parser.parse_args()))

    object.__setattr__(params, '__proto__', proto)
    return params


# noinspection PyUnusedLocal
def proto_signature(parameter_prototype, need_self=False):
    def decorate(f):
        if need_self is True:
            print('ha')
        # Need to have return type as well.
        __doc__ = f.__doc__
        arg_spec = ', '.join(
            ["{k}=parameter_prototype.__dict__['{k}']".format(k=k) for k in parameter_prototype.__dict__.keys() if
             not is_hidden(k)])
        # ["{k}=parameter_prototype.__dict__['{k}'][0]".format(k=k) for k in parameter_prototype.__dict__.keys() if not is_hidden(k)])
        if need_self:
            arg_spec = "self, " + arg_spec
        expr = \
            "def meta_fn({argspec}):\n" \
            "    pass\n" \
            "__signature__ = inspect.signature(meta_fn)\n".format(argspec=arg_spec)
        exec(expr, dict(inspect=inspect, Proto=parameter_prototype), locals())
        f.__signature__ = locals()['__signature__']
        return f

    return decorate
