# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
TODO
"""
__docformat__ = 'restructuredtext'

from nipy.fixes.scipy.stats.models.model import Model

class Classifier(Model):
    """
    TODO
    """
    def learn(self, **keywords):
        """
        :Parameters:
            keywords : ``dict``
                TODO

        :Returns: ``None``
        """
        self.fit(**keywords)
        
