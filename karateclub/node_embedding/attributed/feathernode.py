import numpy as np
import networkx as nx
from scipy.sparse import coo_matrix
from karateclub.estimator import Estimator
from sklearn.decomposition import TruncatedSVD

class FeatherNode(Estimator):
    r"""An implementation of `"TADW" <https://www.ijcai.org/Proceedings/15/Papers/299.pdf>`_
    from the IJCAI '15 paper "Network Representation Learning with Rich Text Information". The
    procedure uses the node attribute matrix with a factorization matrix to reproduce a power
    of the adjacency matrix to create representations.

    Args:
        dimensions (int): Number of embedding dimensions. Default is 32.
        reduction_dimensions (int): SVD reduction dimensions. Default is 64.
        svd_iterations (int): SVD iteration count. Default is 20.
        seed (int): Random seed. Default is 42.
        theta_max (float): Maximal evaluation point. Default is 2.5.
        eval_points (int): Number of characteristic function evaluation points. Default is 25.
        order (int): Scale - number of adjacency matrix powers. Default is 5.
    """
    def __init__(self, dimensions=32, reduction_dimensions=64, svd_iterations=20,
                 seed=42, theta_max=2.5, eval_points=25, order=5):
        self.dimensions = dimensions
        self.reduction_dimensions = reduction_dimensions
        self.svd_iterations = svd_iterations
        self.seed = seed
        self.theta_max = theta_max
        self.eval_points = eval_points
        self.order = order

    def _create_D_inverse(self, graph):
        """
        Creating a sparse inverse degree matrix.
        
        Arg types:
            * **graph** *(NetworkX graph)* - The graph to be embedded.
        Return types:
            * **D_inverse** *(Scipy array)* - Diagonal inverse degree matrix.
        """
        index = np.arange(graph.number_of_nodes())
        values = np.array([1.0/graph.degree[node] for node in range(graph.number_of_nodes())])
        shape = (graph.number_of_nodes(), graph.number_of_nodes())
        D_inverse = sparse.coo_matrix((values, (index, index)), shape=shape)
        return D_inverse

    def _create_A_tilde(self, graph):
        """
        Creating a sparse normalized adjacency matrix.
        
        Arg types:
            * **graph** *(NetworkX graph)* - The graph to be embedded.
        Return types:
            * **A_tilde** *(Scipy array)* - The normalized adjacency matrix.
        """
        A = nx.adjacency_matrix(graph, nodelist = range(graph.number_of_nodes()))
        D_inverse = self._create_D_inverse(graph) 
        A_tilde = D_inverse.dot(A)
        return A_tilde



    def _create_reduced_features(self, X):
        """
        Creating a dense reduced node feature matrix.

        Arg types:
            * **X** *(Scipy COO or Numpy array)* - The wide feature matrix.

        Return types:
            * **X** *(Numpy array)* - The reduced feature matrix of nodes.
        """
        svd = TruncatedSVD(n_components=self.reduction_dimensions,
                           n_iter=self.svd_iterations,
                           random_state=self.seed)
        svd.fit(X)
        X = svd.transform(X)
        return X

    def fit(self, graph, X):
        """
        Fitting a TADW model.

        Arg types:
            * **graph** *(NetworkX graph)* - The graph to be embedded.
            * **X** *(Scipy COO or Numpy array)* - The matrix of node features.
        """
        self._check_graph(graph)
        X = self._create_reduced_features(X)
        theta = np.linspace(0.01, self.theta_max, self.eval_points)
        A_tilde = self._create_A_tilde(graph)
        X = np.outer(X, theta)
        X = X.reshape(graph.number_of_nodes(), -1)
        X = np.concatenate([np.cos(X), np.sin(X)], axis=1)
        feature_blocks = []
        for _ in range(self.order):
            X = A_tilde.dot(X)
            feature_blocks.append(X)
        self._X = np.concatenate(feature_blocks, axis=1)

