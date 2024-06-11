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


def get_class_name(func, *args) -> str:
    """Returns the class name of the object that a method belongs to.

    - If `func` is a bound method, extracts the class name directly from the method.
    - If `func` is an unbound method and `args` are provided, assumes the first argument is `self` and extracts the class name.
    - Returns an empty string if neither condition is met.
    """
    if inspect.ismethod(func):
        return func.__self__.__class__.__name__

    if inspect.isfunction(func) and "self" in inspect.signature(func).parameters and args:
        return args[0].__class__.__name__

    return ""


def get_func_or_method_name(func, *args) -> str:
    """Function name, or method name with class name."""
    cls_name = get_class_name(func, *args)

    return f"{cls_name}.{func.__name__}" if cls_name else f"{func.__name__}"
