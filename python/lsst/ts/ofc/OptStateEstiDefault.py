class OptStateEstiDefault(object):

    def estiOptState(self, optStateEstiData, filterType, wfErr, fieldIdx):
        """Estimate the optical state in the basis of degree of
        freedom (DOF).

        Parameters
        ----------
        optStateEstiData: OptStateEstiDataDecorator
            Instance of OptStateEstiDataDecorator class that holds the DataShare instance.
        filterType : enum 'FilterType'
            Active filter type.
        wfErr : numpy.ndarray
            Wavefront error im um.
        fieldIdx : numpy.ndarray[int] or list[int]
            Field index array.

        Returns
        -------
        numpy.ndarray
            Optical state in the basis of DOF.
        """
        raise NotImplementedError("Should have the child class implemented this.")

if __name__ == "__main__":
    pass
