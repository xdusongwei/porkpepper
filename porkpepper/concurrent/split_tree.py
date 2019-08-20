from collections import defaultdict
import bisect


class SplitTree:
    MAX_DEPTH = 15

    def find(self, hash_integer: int):
        hash_integer = hash_integer % 2 ** 32
        index = bisect.bisect_left(self.nodes, (hash_integer,))
        index = max(index - 1, 0)
        return index

    def __init__(self):
        nodes = [(0, 2 ** 32, 1), ].copy()
        self.nodes = nodes
        self.split_level = 1
        self.merge_level = 1
        self.level_set = defaultdict(set)
        self.merge_pairs = defaultdict(set)
        self.level_set[1].add((0, 2 ** 32, 1))
        self.set_level()

    def clear(self):
        self.nodes.clear()
        self.merge_pairs.clear()
        self.level_set.clear()
        nodes = [(0, 2 ** 32, 1), ]
        self.nodes = nodes
        self.level_set[1].add((0, 2 ** 32, 1))
        self.set_level()

    def set_level(self):
        self.split_level = min([key for key in self.level_set.keys() if self.level_set[key]])
        self.merge_level = max([key for key in self.level_set.keys() if self.level_set[key]])

    def __repr__(self):
        return f"<SplitTree {self.split_level}:{self.merge_level}, {len(self.nodes)}>"

    def split(self):
        if self.split_level >= self.MAX_DEPTH:
            return None
        level = self.split_level
        if not self.level_set[level]:
            return
        node = self.level_set[level].pop()
        split_index = self.nodes.index(node)
        b, e, level = node
        new_level = level + 1
        middle = b + ((e - b) // 2)
        left_node = (b, middle, new_level,)
        right_node = (middle, e, new_level,)
        self.nodes.pop(split_index)
        self.nodes.insert(split_index, right_node)
        self.nodes.insert(split_index, left_node)

        self.merge_pairs[new_level].add((left_node, right_node,))
        self.level_set[new_level].add(left_node)
        self.level_set[new_level].add(right_node)
        self.set_level()
        return node

    def merge(self):
        if self.merge_level <= 1:
            return None
        level = self.merge_level
        if not self.merge_pairs[level]:
            return None
        pair = self.merge_pairs[level].pop()
        left_node, right_node = pair
        merge_index = self.nodes.index(left_node)
        node = (left_node[0], right_node[1], self.merge_level - 1)
        self.nodes.pop(merge_index)
        self.nodes.pop(merge_index)
        self.nodes.insert(merge_index, node)

        self.level_set[node[2]].add(node)
        self.level_set[left_node[2]].remove(left_node)
        self.level_set[right_node[2]].remove(right_node)
        self.set_level()
        return node


__all__ = ['SplitTree', ]
