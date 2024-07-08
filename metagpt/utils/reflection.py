"""class tools, including method inspection, class attributes, inheritance relationships, etc."""


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
