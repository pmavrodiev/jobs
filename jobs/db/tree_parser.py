#! /home/pmavrodiev/anaconda2/bin/python
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 11 14:08:25 2016

@author: Pavlin Mavrodiev
"""

from basic_tree import Tree
from basic_tree import _ROOT
from basic_tree import sanitize_id
from custom_logging import setup_custom_logger

import csv
import logging
# logger = logging.getLogger('root')


class TreeParser(Tree):

    LOGGING_LEVEL = logging.WARNING
    logger = setup_custom_logger('TreeParser', LOGGING_LEVEL)

    def __init__(self, fname, cache_file=None):
        super(TreeParser, self).__init__()
        self.filename = fname
        self.initialized = False

    # count
    def __sum_node_data(self, node_identifier, **kwargs):

        nuts3 = kwargs.pop("nuts3", None)
        nuts4 = kwargs.pop("nuts4", None)
        _sum = 0

        # if no job from any (nuts3, nuts4) has been added to this category
        # return 0

        if not self[node_identifier].data:
            return _sum
        """
        if self.is_root(node_identifier):
            return self[node_identifier].data
        """
        if (not nuts3) and (not nuts4):
            for nuts3 in self[node_identifier].data:
                for nuts4 in self[node_identifier].data[nuts3]:
                    _sum = _sum + self[node_identifier].data[nuts3][nuts4]
        #
        elif nuts3 and not nuts4:
            if nuts3 in self[node_identifier].data:
                for nuts4 in self[node_identifier].data[nuts3]:
                    _sum = _sum + self[node_identifier].data[nuts3][nuts4]
        #
        elif nuts3 and nuts4:
            if nuts3 in self[node_identifier].data:
                if nuts4 in self[node_identifier].data[nuts3]:
                    _sum = _sum + self[node_identifier].data[nuts3][nuts4]
        else:
            # not nuts3 and nuts4
            TreeParser.logger.error("Cannot request nuts4 without specifying "
                                    "nuts3 ")
            return None
        #
        return _sum

    # prints the parents of node_identifier in hierarchical order, i.e.
    # starting with the most distant ancestor
    def get_branch(self, node_identifier, **kwargs):
        branch_str = self[node_identifier].name
        parent = self[node_identifier].parent_pointer
        while parent:
            parent_node = self[parent]
            parent = parent_node.parent_pointer
            # skip the root
            if not parent:
                break
            branch_str = parent_node.name + "-" + branch_str
        #
        summed_node_data = self.__sum_node_data(node_identifier, **kwargs)
        if summed_node_data is None:
            return None

        branch_str = branch_str + ";" + str(round(summed_node_data, 1))
        return branch_str

    # display the tree depth-first
    def show(self, start_node, level=_ROOT):
        queue = self[start_node].children_pointer
        if level == _ROOT:
            print("%s [%s]" % (self[start_node].name,
                               self[start_node].identifier))
        else:
            print("\t"*level + "%s [%s] " %
                  (self[start_node].name,
                   self[start_node].identifier))
        if self[start_node].expanded:
            level += 1
            for element in queue:
                self.show(element, level)  # recursive call

    def __read_csv_description(self):
        try:
            in_tree = open(self.filename, 'r')
            return csv.reader(in_tree, delimiter=";")
        except IOError as e:
            TreeParser.logger.error("%s", e)
            return None

    def get_most_similar(self, node_identifier):
        for n in self.nodes:
            if node_identifier in self[n].identifier:
                return n
        return None

    def __tokenize_nodename(self, name):
        # example: Технологии (Четвъртичен сектор)
        main_name = None
        alt_name = None
        first_parenthesis = name.find("[")
        last_parenthesis = name.rfind("]")
        if first_parenthesis == -1 or last_parenthesis == -1:
            main_name = name.strip()
            return (main_name, alt_name)

        main_name = name[0: first_parenthesis].strip()
        alt_name = name[first_parenthesis+1: last_parenthesis].strip()
        # check the encoding, we want utf-8
        if type(main_name) == unicode:
            main_name = main_name.encode('utf-8')
        if type(alt_name) == unicode:
            alt_name = alt_name.encode('utf-8')

        TreeParser.logger.debug("Tokenized %s -> %s", main_name, alt_name)
        return (main_name, alt_name)

    def build_tree(self):
        csv = self.__read_csv_description()
        if not csv:
            return

        # create the ROOT node
        self.add_node("ROOT", alternative_name="ROOT", identifier="root")

        for row in csv:
            last_scanned = None
            # each n in row should be a tree node
            for idx, node in enumerate(row):
                # example: Технологии (Четвъртичен сектор)
                # (node_name, alternative_name)=(Технологии,Четвъртичен сектор)
                (node_name, alternative_name) = self.__tokenize_nodename(node)
                # row[0] should always have ROOT as parent
                parent = "root" if idx == 0 else last_scanned
                unique_id = node_name if parent == "root" else parent + node_name
                self.add_node(node_name, alternative_name,
                              identifier=sanitize_id(unique_id),
                              parent_identifier=parent)
                last_scanned = sanitize_id(unique_id)
                #
        self.initialized = True



if __name__ == "__main__":
    tp = TreeParser("jobCategories.txt")
    tp.build_tree()

    print("="*80)
    tp.show("root")
    print("="*80)


