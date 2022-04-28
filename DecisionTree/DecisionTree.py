# from hashlib import new
import numpy as np
# from typing import Iterable, Mapping, Tuple, TypeVar
# import metrics as m
from metrics import *

# TODO LIST
# TODO : Initialization method for uninitialized DT parameters
# TODO : post-pruning with a threshold for a metric gain
# TODO : max leaves stop splitting
# TODO : write desiciontrees for classification, regression.



# T = TypeVar('T', int, float, str)
#
# List = TypeVar('List', list, np.array)

BIG_CONST = 9999999
SMALL_CONST = -9999999
LEAF_FLAG = -1
UNKNOWN_FLAG = None


METRICS = {
    'ig': information_gain,
    'gini': gini_impurity,
    'mse': mse,
    'mae': mae,
    'rmse': rmse
}

METRICS_METHOD_OPTIMIZATION = {
    'ig': 'max',
    'gini': 'min',
    'mse': 'min',
    'mae': 'min',
    'rmse': 'min'
}

COMPARISON_FUNCTIONS = {
    'max': lambda old, new: old < new,
    'min': lambda old, new: old > new
}


class Node:

    def __init__(self,
                 sample_indexes=None,
                 targets=None,
                 depth=None,
                 node_number=None):
        self.sample_indexes = sample_indexes
        self.targets = targets
        self.depth = depth
        self.node_number = node_number

        self.left = LEAF_FLAG
        self.right = LEAF_FLAG
        self.split_column = None
        self.split_value = None
        self.metric_value = None

    def is_leaf(self):
        return True if self.left is LEAF_FLAG and self.right is LEAF_FLAG else False


class DecisionTree:
    def __init__(self,
                 max_depth=10,
                 max_leaves=1024,
                 min_sample_size_in_leaf=1,
                 min_split_sample=2,

                 split_metric='ig',
                 split_type='q'):

        self.min_sample_size_in_leaf = min_sample_size_in_leaf
        self.min_split_sample = min_split_sample
        self.split_metric = split_metric
        self.max_leaves = max_leaves
        self.max_depth = max_depth
        self.classes = None
        self.split_type = split_type

        self.metric_function = METRICS[self.split_metric]
        self.metric_method_optimization = METRICS_METHOD_OPTIMIZATION[self.split_metric]
        self.comparison_function = COMPARISON_FUNCTIONS[self.metric_method_optimization]
        self._best_split_initialization = SMALL_CONST if self.metric_method_optimization == 'max' else BIG_CONST
        self.tree_ = None
        self.tree_stack_ = []

    @staticmethod
    def _sort_matrix(matrix, sort_by_col=0):
        sorted_matrix = matrix[matrix[:, sort_by_col].argsort()]
        return sorted_matrix

    @staticmethod
    def _split(feature_values, split_value):
        # print(feature_values, split_value)
        left_sample_index = np.where(feature_values <= split_value)[0]
        right_sample_index = np.where(feature_values > split_value)[0]
        return left_sample_index, right_sample_index

    @staticmethod
    def _get_tree_stack(in_node):
        stack = [in_node]
        for node in stack:
            if node == LEAF_FLAG:
                stack.append(UNKNOWN_FLAG)
                stack.append(UNKNOWN_FLAG)
            elif node is None:
                continue
            else:
                stack.append(node.left)
                stack.append(node.right)
        return stack

    def _get_f_values(self, input_vector):
        '''
        takes an input vector of numbers and if amount of unique values are more than 10
        returns 0.1, 0.2...1 quantile of the vector
        '''
        if self.split_type == 'q':
            split_values = np.histogram(input_vector, bins=10)[1]
        elif self.split_type == 'all':
            split_values = input_vector
        return split_values

    def _find_best_split(self, feature_values, targets):
        pass


    def _get_best_node(self, sample, targets, indexes):
        nrof_columns = sample.shape[1]

        # initialize best_metric_value with the pervios node best metric value
        best_metric_value = self._best_split_initialization
        best_col_for_split = None
        best_split_value = None

        for col_idx in range(nrof_columns):
            col_split_value, col_metric_value = self._find_best_split(sample[indexes, col_idx], targets[indexes])

            if self.comparison_function(best_metric_value, col_metric_value):
                best_split_value = col_split_value
                best_metric_value = col_metric_value
                best_col_for_split = col_idx

        left_index, right_index = self._split(sample[indexes, best_col_for_split], best_split_value)
        left_index = indexes[left_index]
        right_index = indexes[right_index]

        return left_index, right_index, best_col_for_split, best_split_value, best_metric_value

    def display_tree(self):
        stack = self._get_tree_stack(self.tree_)
        thresholds = []
        cols = []
        values = []

        for current_node in stack:
            if isinstance(current_node, Node):
                thresholds.append(current_node.split_value)
                cols.append(current_node.split_column)
                values.append(np.mean(current_node.targets))

        return cols, thresholds, values

    def check_sample_suit(self, depth, sample_indexes, leaves_counter):
        MINIMAL_RESIDUAL_LEAVES = 2

        is_sample_suitable = True
        sample_size = len(sample_indexes)

        if depth >= self.max_depth:
            is_sample_suitable = False
        elif sample_size <= self.min_split_sample:
            is_sample_suitable = False
        elif (self.max_leaves - leaves_counter) <= MINIMAL_RESIDUAL_LEAVES:
            is_sample_suitable = False

        return is_sample_suitable

    def build_tree(self, sample, targets):
        sample_indexes = np.array(range(sample.shape[0]))
        root = Node(sample_indexes=sample_indexes, targets=targets, depth=1, node_number=0)

        self.tree_stack_.append(root)

        leaves_counter = 0

        for current_node in self.tree_stack_:
            split_params = self._get_best_node(sample,
                                               targets,
                                               current_node.sample_indexes)

            left_index, right_index, best_col, split_value, best_metric = split_params

            current_node.split_column = best_col
            current_node.split_value = split_value
            current_node.metric_value = best_metric

            next_depth = current_node.depth + 1
            parent_node_number = current_node.node_number

            current_node.left = Node(sample_indexes=left_index,
                                     targets=targets[left_index],
                                     depth=next_depth,
                                     node_number=parent_node_number + 1)

            current_node.right = Node(sample_indexes=right_index,
                                      targets=targets[right_index],
                                      depth=next_depth,
                                      node_number=parent_node_number + 2)

            if self.check_sample_suit(next_depth, left_index, leaves_counter):
                self.tree_stack_.append(current_node.left)
            else:
                leaves_counter += 1

            if self.check_sample_suit(next_depth, right_index, leaves_counter):
                self.tree_stack_.append(current_node.right)
            else:
                leaves_counter += 1

        return root

    def fit(self, X_train, y_train):
        pass

    def _node_predict(self, node, sample, indexes):
        pass


    def predict(self, data):
        pass

class DecisionTreeClassifier(DecisionTree):
    def __init__(self, *args, **kwargs):
        super(DecisionTreeClassifier, self).__init__(*args, **kwargs)



    def _find_best_split(self, feature_values, targets):
        sorted_matrix = np.dstack([feature_values, targets])[0]
        sorted_matrix = self._sort_matrix(sorted_matrix)

        best_metric_value = self._best_split_initialization
        best_split_value = None

        split_values = self._get_f_values(feature_values)

        for f_value in split_values:
            left_sample_index, right_sample_index = self._split(feature_values, f_value)

            if len(left_sample_index) < self.min_sample_size_in_leaf:
                continue
            elif len(right_sample_index) < self.min_sample_size_in_leaf:
                continue

            parent_freqs = get_freqs(sorted_matrix[:, 1], self.classes)
            left_freqs = get_freqs(sorted_matrix[left_sample_index, 1], self.classes)
            right_freqs = get_freqs(sorted_matrix[right_sample_index, 1], self.classes)

            cur_metric_value = self.metric_function(parent_freqs, left_freqs, right_freqs)

            if self.comparison_function(best_metric_value, cur_metric_value):
                best_metric_value = cur_metric_value
                best_split_value = f_value

        return best_split_value, best_metric_value

    def fit(self, X_train, y_train):
        self.classes = np.unique(y_train)
        self.tree_ = self.build_tree(X_train, y_train)

    def _node_predict(self, node, sample, indexes):
        if node.is_leaf():
            probs = get_freqs(node.targets, self.classes)
            probs = probs.reshape((len(self.classes), 1))
            result = (np.ones(sample.shape[0]) * probs).T
            return result, indexes

        left_sample_indexes, right_sample_indexes = self._split(sample[:, node.split_column], node.split_value)

        left_result, left_sample_indexes = self._node_predict(node.left,
                                                              sample[left_sample_indexes],
                                                              left_sample_indexes)

        right_result, right_sample_indexes = self._node_predict(node.right,
                                                                sample[right_sample_indexes],
                                                                right_sample_indexes)

        left_sample_indexes = indexes[left_sample_indexes]
        right_sample_indexes = indexes[right_sample_indexes]

        # print('LR', left_result, right_result)
        parent_result = np.concatenate([left_result, right_result])
        parent_indexes = np.concatenate([left_sample_indexes, right_sample_indexes])

        return parent_result, parent_indexes

    def predict(self, data):
        indexes = np.array(list(range(data.shape[0])))
        results, parent_indexes = self._node_predict(self.tree_, data, indexes)
        # print(len(results), len(parent_indexes))
        sorted_results = np.column_stack([parent_indexes, results])
        sorted_results = self._sort_matrix(sorted_results, sort_by_col=0)
        return sorted_results[:, 1:]


class DecisionTreeRegressor(DecisionTree):
    def __init__(self, *args, **kwargs):
        super(DecisionTreeRegressor, self).__init__(*args, **kwargs)

    def _find_best_split(self, feature_values, targets):
        sorted_matrix = np.dstack([feature_values, targets])[0]
        sorted_matrix = self._sort_matrix(sorted_matrix)

        best_metric_value = self._best_split_initialization
        best_split_value = None

        split_values = self._get_f_values(feature_values)

        for f_value in split_values:
            left_sample_index, right_sample_index = self._split(feature_values, f_value)

            if len(left_sample_index) < self.min_sample_size_in_leaf:
                continue
            elif len(right_sample_index) < self.min_sample_size_in_leaf:
                continue

            parent_predict_value = np.array([sorted_matrix[:, 1].mean()])
            left_predict_value = np.array([sorted_matrix[left_sample_index, 1].mean()])
            right_predict_value = np.array([sorted_matrix[right_sample_index, 1].mean()])

            parent_metric = self.metric_function(sorted_matrix[:, 1], parent_predict_value)
            left_metric = self.metric_function(sorted_matrix[left_sample_index, 1], left_predict_value)
            right_metric = self.metric_function(sorted_matrix[right_sample_index, 1], right_predict_value)

            mean_l_r_metric = (left_metric + right_metric) / 2

            if self.comparison_function(parent_metric, mean_l_r_metric) and self.comparison_function(best_metric_value, mean_l_r_metric):
                best_metric_value = mean_l_r_metric
                best_split_value = f_value

        return best_split_value, best_metric_value

    def fit(self, X_train, y_train):
        self.tree_ = self.build_tree(X_train, y_train)

    def _node_predict(self, node, sample, indexes):
        if node.is_leaf():
            result = np.ones(sample.shape[0]) * node.targets.mean()
            return result, indexes

        left_sample_indexes, right_sample_indexes = self._split(sample[:, node.split_column], node.split_value)

        left_result, left_sample_indexes = self._node_predict(node.left,
                                                              sample[left_sample_indexes],
                                                              left_sample_indexes)

        right_result, right_sample_indexes = self._node_predict(node.right,
                                                                sample[right_sample_indexes],
                                                                right_sample_indexes)

        left_sample_indexes = indexes[left_sample_indexes]
        right_sample_indexes = indexes[right_sample_indexes]

        # print('LR', left_result, right_result)
        parent_result = np.concatenate([left_result, right_result])
        parent_indexes = np.concatenate([left_sample_indexes, right_sample_indexes])

        return parent_result, parent_indexes

    def predict(self, data):
        indexes = np.array(list(range(data.shape[0])))

        results, parent_indexes = self._node_predict(self.tree_, data, indexes)
        # print(len(results), len(parent_indexes))
        sorted_results = np.column_stack([parent_indexes, results])
        sorted_results = self._sort_matrix(sorted_results, sort_by_col=0)
        return sorted_results[:, 1:]
