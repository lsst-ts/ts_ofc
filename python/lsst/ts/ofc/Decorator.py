class Decorator(object):

    def __init__(self, decoratedObj):
        """Initialization of decorator class.

        Parameters
        ----------
        decoratedObj : obj
            Decorated object.
        """

        self.__decoratedObj = decoratedObj

    def __getattr__(self, attributeName):
        """Use the functions and attributes hold by the object.

        Parameters
        ----------
        attributeName : str
          Name of attribute or function.

        Returns
        -------
        obj
          Returned values.
        """

        return getattr(self.__decoratedObj, attributeName)


if __name__ == "__main__":
    pass
