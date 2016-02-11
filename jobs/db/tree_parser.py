#! /home/pmavrodiev/anaconda2/bin/python
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 11 14:08:25 2016

@author: Pavlin Mavrodiev
"""

from basic_tree import Tree
from basic_tree import _ROOT
from basic_tree import sanitize_id
import logging
import csv


class TreeParser(Tree):

    # set up the logger
    LOGGING_LEVEL = logging.ERROR
    logging.basicConfig(level=LOGGING_LEVEL)
    logger = logging.getLogger('tree_parser')

    def __init__(self, fname):
        super(TreeParser, self).__init__()
        self.filename = fname
        self.initialized = False

    # count
    def count_node_data(self, node_identifier):
        count = 0
        if self[node_identifier].data:
            for nuts3 in self[node_identifier].data:
                for nuts4 in self[node_identifier].data[nuts3]:
                    count = count + self[node_identifier].data[nuts3][nuts4]
        return count

    # display the tree depth-first
    def show(self, start_node, level=_ROOT):
        queue = self[start_node].children_pointer
        if level == _ROOT:
            print("%s [%s]" % (self[start_node].name,
                               self[start_node].identifier))
        else:
            print("\t"*level + "%s [%s] %d" %
                  (self[start_node].name,
                   self[start_node].identifier,
                   self.count_node_data(start_node)))
        if self[start_node].expanded:
            level += 1
            for element in queue:
                self.show(element, level)  # recursive call


    def __read_csv_description(self):
        try:
            in_tree = open(self.filename, 'r')
            return csv.reader(in_tree, delimiter=";")
        except IOError as e:
            self.logger.error("%s", e)
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
                self.add_node(node_name, alternative_name,
                              identifier=sanitize_id(node_name),
                              parent_identifier=parent)
                last_scanned = node_name
                #
        self.initialized = True

"""

if __name__ == "__main__":
    tp = TreeParser("jobCategories.txt")
    tp.build_tree()

    print("="*80)
    tp.show("root")
    print("="*80)


    for node in tp.expand_tree("root", mode=1):
        print(node)
"""
