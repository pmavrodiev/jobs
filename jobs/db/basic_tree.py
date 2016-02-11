#! /home/pmavrodiev/anaconda2/bin/python
# -*- coding: utf-8 -*-

"""
Created on Wed Feb 10 17:53:54 2016

@author: Pavlin Mavrodiev

This tree class is taken from one of the answers to this question
http://stackoverflow.com/questions/2482602/a-general-tree-implementation-in-python

Alternatively the original source code should be available here:
http://www.quesucede.com/page/show/id/python_3_tree_implementation

"""

import uuid
import re

(_ADD, _DELETE, _INSERT) = range(3)
(_ROOT, _DEPTH, _WIDTH) = range(3)

# compile a regex that removes all white spaces from a string,
# including the annoying \xa0 (non-breaking space in Latin1 ISO 8859-1)
nowhitespaces = re.compile(r"[\xa0\s+]")


def sanitize_id(id):

    import string
    id = str(id).translate(string.maketrans("", ""),
                           string.punctuation).decode("utf-8").lower()

    return nowhitespaces.sub("", id).encode("utf-8")


class Node:

    def __init__(self, name, alternative_name=None, identifier=None,
                 expanded=True):
        self.__identifier = (str(uuid.uuid1()) if identifier is None else
                             sanitize_id(identifier))
        self.name = name
        self.altname = alternative_name
        self.expanded = expanded
        self.__parent_pointer = None  # pointer to parent
        self.__children_pointer = []  # pointer to the children
        self.data = None  # potential payload

    @property
    def identifier(self):
        return self.__identifier

    @property
    def children_pointer(self):
        return self.__children_pointer

    @children_pointer.setter
    def children_pointer(self, value):
        if value is not None and isinstance(value, list):
            self.__children_pointer = value

    @property
    def parent_pointer(self):
        return self.__parent_pointer

    @parent_pointer.setter
    def parent_pointer(self, value):
        if value is not None:
            self.__parent_pointer = sanitize_id(value)

    def update_children_pointer(self, identifier, mode=_ADD):
        # append node to the children of the parent
        if mode is _ADD:
            self.__children_pointer.append(sanitize_id(identifier))
        # remove node from the children of the parent
        elif mode is _DELETE:
            self.__children_pointer.remove(sanitize_id(identifier))
        # replace the children of the parent with this node
        elif mode is _INSERT:
            self.__children_pointer = [sanitize_id(identifier)]


class Tree(object):

    def __init__(self):
        self.nodes = {}

    # add a new node to the tree
    def add_node(self, name, alternative_name=None,
                 identifier=None, parent_identifier=None):

        node = Node(name, alternative_name, identifier)
        try:
            self.nodes[identifier]
        except KeyError:
            self.nodes[identifier] = node
            # add this node to children of its parent
            self.__update_children_pointer(parent_identifier,
                                           node.identifier, _ADD)
            node.parent_pointer = parent_identifier

    # update the children pointer of target_node with this_node
    def __update_children_pointer(self, target_node, this_node, mode):
        # if this node is Root, no parent needs to be updated
        if target_node is None:
            return
        else:
            # get a handle to the parent
            self[target_node].update_children_pointer(this_node, mode)

    # makes this_node the parent of target_node
    def __update_parent_pointer(self, target_node, this_node):
        self[target_node].parent_pointer = this_node

    def expand_tree(self, start_node, mode=_DEPTH):
        # Python generator. Loosly based on an algorithm from 'Essential LISP'
        # by John R. Anderson, Albert T. Corbett, and Brian J. Reiser
        # page 239-241
        yield start_node

        queue = self[start_node].children_pointer
        while queue:
            yield queue[0]
            expansion = self[queue[0]].children_pointer
            if mode is _DEPTH:
                queue = expansion + queue[1:]  # depth-first
            elif mode is _WIDTH:
                queue = queue[1:] + expansion  # breadth-first

    # returh the children of this_node
    def is_branch(self, this_node):
        return self[this_node].children_pointer

    def __getitem__(self, node_identifier):
        return self.nodes.get(sanitize_id(node_identifier))

    def __setitem__(self, node_identifier, node):
        self.nodes.update({sanitize_id(node_identifier): node})

    def __len__(self):
        return len(self.nodes)

    def __contains__(self, node_identifier):
        return sanitize_id(node_identifier) in self.nodes



if __name__ == "__main__":

    tree = Tree()
    tree.add_node("Harry", identifier="harry")  # root node
    tree.add_node("Jane", identifier="jane", parent_identifier="harry")
    tree.add_node("Bill", identifier="bill", parent_identifier="harry")
    tree.add_node("Joe", identifier="joe", parent_identifier="jane")
    tree.add_node("Diane", identifier="diane", parent_identifier="jane")
    tree.add_node("George", identifier="george", parent_identifier="diane")
    tree.add_node("Mary", identifier="mary", parent_identifier="diane")
    tree.add_node("Jill", identifier="jill", parent_identifier="george")
    tree.add_node("Carol", identifier="carol", parent_identifier="jill")
    tree.add_node("Grace", identifier="grace", parent_identifier="bill")
    tree.add_node("Mark", identifier="mark", parent_identifier="jane")



    # print("="*80)
    # tree.show("harry")
    # print("="*80)

    for node in tree.expand_tree("harry", mode=_DEPTH):
        print(node)
    print("="*80)


