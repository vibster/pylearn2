"""
Unit tests for ../sparse_dataset.py
"""

import numpy as np
from pylearn2.datasets.sparse_dataset import SparseDataset
from pylearn2.training_algorithms.default import DefaultTrainingAlgorithm
from pylearn2.train import Train
from pylearn2.models.model import Model
from pylearn2.space import VectorSpace
from pylearn2.termination_criteria import EpochCounter
from scipy.sparse import csr_matrix
from pylearn2.costs.cost import Cost, DefaultDataSpecsMixin
from pylearn2.training_algorithms.sgd import SGD
from pylearn2.utils import sharedX
from pylearn2.utils import wraps
import theano.tensor as T


class SoftmaxModel(Model):
    """
    A dummy model used for testing.

    Parameters
    ----------
    dim : int
        the input dimension of the Softmax Model

    Notes
    -----
    Important properties:
    has a parameter (P) for SGD to act on
    has a get_output_space method, so it can tell the
    algorithm what kind of space the targets for supervised
    learning live in
    has a get_input_space method, so it can tell the
    algorithm what kind of space the features live in
    """
    def __init__(self, dim):
        self.dim = dim
        rng = np.random.RandomState([2014, 4, 22])
        self.P = sharedX(rng.uniform(-1., 1., (dim,)))
        self.force_batch_size = None

    @wraps(Model.get_params)
    def get_params(self):
        return [self.P]

    @wraps(Model.get_input_space)
    def get_input_space(self):
        return VectorSpace(self.dim)

    @wraps(Model.get_output_space)
    def get_output_space(self):
        return VectorSpace(self.dim)

    def __call__(self, X):
        """
        Compute and return the softmax transformation of sparse data.
        """
        assert X.ndim == 2
        return T.nnet.softmax(X*self.P)


class DummyCost(DefaultDataSpecsMixin, Cost):
    """
    A dummy cost used for testing.

    Parameters
    ----------
    No parameters is required for this class.

    Notes
    -----
    Important properties:
    has a expr method which takes a model and a
    dataset and returns as cost the mean squared
    difference between the data and the models'
    output using that data.
    """
    @wraps(Cost.expr)
    def expr(self, model, data):
        """
        returns as cost the mean squared
        difference between the data and the models'
        output using that data.
        """
        space, sources = self.get_data_specs(model)
        space.validate(data)
        X = data
        return T.square(model(X) - X).mean()

    @wraps(DefaultDataSpecsMixin.get_data_specs)
    def get_data_specs(self, model):
        """
        Returns the tuple of (space, source) of the model.

        Parameters
        ----------
        model : Model
            The model to train with this cost

        Returns
        -------
        data_specs : tuple
            The tuple should be of length two.
            The first element of the tuple should be a Space (possibly a
            CompositeSpace) describing how to format the data.
            The second element of the tuple describes the source of the
            data. It probably should be a string or nested tuple of strings.
        """
        return super(DummyCost, self).get_data_specs(model)


def test_iterator():
    """
    tests wether SparseDataset can be loaded and
    initializes iterator
    """

    x = csr_matrix([[1, 2, 0], [0, 0, 3], [4, 0, 5]])
    ds = SparseDataset(from_scipy_sparse_dataset=x)
    it = ds.iterator(mode='sequential', batch_size=1)
    it.next()


def test_training_a_model():
    """
    tests wether SparseDataset can be trained
    with a dummy model.
    """

    dim = 3
    m = 10
    rng = np.random.RandomState([22, 4, 2014])

    X = rng.randn(m, dim)
    ds = csr_matrix(X)
    dataset = SparseDataset(from_scipy_sparse_dataset=ds)

    model = SoftmaxModel(dim)
    learning_rate = 1e-1
    batch_size = 5

    epoch_num = 2
    termination_criterion = EpochCounter(epoch_num)

    cost = DummyCost()

    algorithm = SGD(learning_rate, cost, batch_size=batch_size,
                    termination_criterion=termination_criterion,
                    update_callbacks=None,
                    init_momentum=None,
                    set_batch_size=False)

    train = Train(dataset, model, algorithm, save_path=None,
                  save_freq=0, extensions=None)

    train.main_loop()

if __name__ == '__main__':
    test_iterator()
    test_training_a_model()
