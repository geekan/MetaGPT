"""class tools, including method inspection, class attributes, inheritance relationships, etc."""
import inspect


def check_methods(C, *methods):
    """Check if the class has methods. borrow from _collections_abc.

    Useful when implementing implicit interfaces, such as defining an abstract class, isinstance can be used for determination without inheritance.
    """
    mro = C.__mro__
    for method in methods:
        for B in mro:
            if method in B.__dict__:
                if B.__dict__[method] is None:
                    return NotImplemented
                break
        else:
            return NotImplemented
    return True


def get_class_name(func) -> str:
    """Returns the class name of the object that a method belongs to.

    - If `func` is a bound method or a class method, extracts the class name directly from the method.
    - Returns an empty string if it's a regular function or cannot determine the class.
    """
    if inspect.ismethod(func):
        if inspect.isclass(func.__self__):
            return func.__self__.__name__

        return func.__self__.__class__.__name__

    if inspect.isfunction(func):
        qualname_parts = func.__qualname__.split(".")
        if len(qualname_parts) > 1:
            class_name = qualname_parts[-2]
            if class_name.isidentifier():
                return class_name

    return ""
