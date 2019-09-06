import bisect
import collections
import math


class Bin:

    __slots__ = ['left', 'right', 'count']

    def __init__(self, left, right, count=1):
        self.left = left
        self.right = right
        self.count = count

    def __add__(self, other):
        return Bin(
            left=min(self.left, other.left),
            right=max(self.right, other.right),
            count=self.count + other.count
        )

    def __lt__(self, other):
        return self.right <= other.left

    def __eq__(self, other):
        return self.left == other.left and self.right == other.right

    def __str__(self):
        return f'[{self.left:.5f}, {self.right:.5f}]: {self.count}'


class Histogram(collections.UserList):
    """Streaming histogram.

    Parameters:
        max_bins (int): Maximal number of bins.

    Attributes:
        n (int): Total number of seen values.

    Example:

        ::

            >>> from creme import utils
            >>> import matplotlib.pyplot as plt
            >>> import numpy as np

            >>> np.random.seed(42)

            >>> values = np.hstack((
            ...     np.random.normal(-3, 1, 1000),
            ...     np.random.normal(3, 1, 1000),
            ... ))

            >>> hist = utils.Histogram(max_bins=60)

            >>> for x in values:
            ...     hist = hist.update(x)

            >>> ax = plt.bar(
            ...     x=[(b.left + b.right) / 2 for b in hist],
            ...     height=[b.count for b in hist],
            ...     width=[(b.right - b.left) / 2 for b in hist]
            ... )

        .. image:: ../_static/histogram_docstring.svg
            :align: center

    References:
        1. `A Streaming Parallel Decision Tree Algorithm <http://jmlr.org/papers/volume11/ben-haim10a/ben-haim10a.pdf>`_
        2. `Go implementation <https://github.com/VividCortex/gohistogram>`_

    """

    def __init__(self, max_bins=256):
        super().__init__()
        self.max_bins = max_bins
        self.n = 0

    def update(self, x):

        self.n += 1

        # Insert the value into the histogram
        b = Bin(left=x, right=x)
        i = bisect.bisect_left(self, b)

        # Insert the bin if the list is empty or the x is to right edge
        if not self or i == len(self):
            self.insert(i, b)
        else:
            # Increment the bin counter if x is part of a bin
            if x >= self[i].left:
                self[i].count += 1
            # Insert the bin if it is between bin i-1 and bin i
            else:
                self.insert(i, b)

        # Bins have to be merged if there are more than max_bins
        if len(self) == self.max_bins + 1:

            # Find the closest bins
            min_val = math.inf
            min_idx = None
            for idx, (b1, b2) in enumerate(zip(self[:-1], self[1:])):
                diff = b2.right - b1.left
                if diff < min_val:
                    min_val = diff
                    min_idx = idx

            # Merge the bins
            self[min_idx] += self.pop(min_idx + 1)

        return self

    def cdf(self, x):
        """Cumulative distribution function.

        Example:

            >>> from creme import utils

            >>> hist = Histogram()
            >>> for x in range(4):
            ...     hist = hist.update(x)

            >>> print(hist)
            [0.00000, 0.00000]: 1
            [1.00000, 1.00000]: 1
            [2.00000, 2.00000]: 1
            [3.00000, 3.00000]: 1

            >>> hist.cdf(0)
            0.25

            >>> hist.cdf(.5)
            0.375

            >>> hist.cdf(1)
            0.5

            >>> hist.cdf(2.5)
            0.875

        """

        # Handle edge cases
        if x < self[0].left:
            return 0.
        elif x >= self[-1].right:
            return 1.

        # Handle the first bin
        c = 0
        b = self[0]
        try:
            c += b.count * (x - b.left) / (b.right - b.left)
        except ZeroDivisionError:
            c += b.count

        # Handle the rest of the bins
        for b1, b2 in zip(self[:-1], self[1:]):
            if x < b2.right:
                # Interpolate
                c += b2.count * (x - b1.right) / (b2.right - b1.right)
                break
            c += b2.count

        return c / self.n

    def __str__(self):
        return '\n'.join(str(b) for b in self)
