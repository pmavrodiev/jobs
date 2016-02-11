#! /home/pmavrodiev/anaconda2/bin/python
# -*- coding: utf-8 -*-
"""
Created on Sat Oct  3 16:43:50 2015

@author: pmavrodiev


The purpose of this module is to extract the nuts3 (province)
and nuts4 (municipality) codes of the location information
given in the job posting.

Note that NUTS = Nomenclature of Territorial Units for Statistics
These codes are then used to visualize a job posting on a geographical map.

To this end, there are 3 available data sources:
  1. *Ek_atte.csv* - this is classification of settlements
     based on the EKATTE (Bulgarian region coding system).
     It contains detailed information on the nuts3 and nuts4:
     ==========================================================
     ekatte   t_v_m   name	    oblast    obstina    kmetstvo
     ==========================================================
     00905,    с.,   Априлци,   KRZ,      KRZ14,    KRZ14-48
     ----------------------------------------------------------

     In this example, the settlement Априлци has nuts3=KRZ and nuts4=KRZ14
     which puts it in province Кърджали and municipality Кирково.

     More on the mapping between nuts3/nuts4 and province/municipality
     names below.

  2. *provinces.csv* - this is a mapping between province names and their
      nuts3 codes. In the example above nuts3=KRZ corresponds to province
      Кърджали

  3. *municipalities.csv* - similarly this is a mapping between
      municipalities names and their corresponding nuts4 codes.

Given these 3 data sources a job posting is processed in the following way.

  1. The job's 'location' and 'location2' fields are extracted from the
     sqlite db. Typically location is the name of a settlement,
     regardless of type, e.g. city, village, resort, etc..

     'location2' is either the country or the province name in the format
     of e.g. Област Варна, i.e. the keyword Област must be discounted.

  2. Search for the location in the EKATTE data.

  2.1. If found and unique, we easily extract the EKATTE
       nuts3 and nuts4 codes. We then use provinces.csv to extract
       the nuts3 code corresponding to 'location2'. If the EKATTE nuts3 code
       and the nuts3 code extracted from provinces.csv do not match, prefer
       the latter, i.e. give preference to the information in the sqlite db.
       Move to the next job posting.

  2.2. If found and *not* unique (i.e. the settlement's name is not unique),
       use provinces.csv to extract the nuts3 code corresponding to
       'location2'. Use this code to differentiate among the duplicate entries.

  2.3. If not found use 'location2' to extract the province.
"""

import csv
from itertools import compress
import logging
import re

# compile a regex that removes all white spaces from a string,
# including the annoying \xa0 (non-breaking space in Latin1 ISO 8859-1)
nowhitespaces = re.compile(r"[\xa0\s+]")


class LocationClassifier:

    # set up the logger
    LOGGING_LEVEL = logging.ERROR
    logging.basicConfig(level=LOGGING_LEVEL)
    logger = logging.getLogger(__name__)

    def __init__(self, ekatte_file, provinces_file):
        self.f_ekatte = ekatte_file
        self.f_provinces = provinces_file
        # data structures
        self.all_jobs = None
        self.ekatte_dict, self.ekatte_locations = self.read_ekatte()
        self. provinces_dict, self. provinces = self.read_provinces()

    def read_ekatte(self):
        """Reads the Ekatte csv file with detailed settlements information.

        Args:
            filename (str): The filename of the csv file

        Returns:
            A tuple of dict and array. The array contains the names of all
            settlements sequentially read from the csv file. Duplicates are
            possible.

            The dictionary has the following format:

                {key: settlement name
                value: dict(key: settlement_type
                            value: [(nuts3, nuts4)]{}

            For example, here are some special cases:

            1. settlements with the same name in the same province
                с.,Крайна, SML, SML16
                с.,Крайна, SML, SML18

               will be stored as
               dict["Крайна"]["c."] = [(SML, SML16), (SML, SML18)]

            2. settlements with the same name and different settlement type
                с.,Габрово,BLG,BLG03,BLG03-00,3,8,7,1901,SW,935
                гр.,Габрово,GAB,GAB05,GAB05-00,1,1,5,1901,N,936
                с.,Габрово,KRZ,KRZ35,KRZ35-03,3,6,8,1901,S,937

               will be stored as
               dict["Габрово"]["гр."] = [(GAB, GAB05)]
               dict["Габрово"]["с."] = [(BLG, BLG03), (KRZ, KRZ35)]
        """
        try:
            ekatte_file = open(self.f_ekatte, 'r')
        except IOError as e:
            self.logging.error("%s", e)
            return (None, None)
        ekatte_csv = csv.reader(ekatte_file, delimiter=',')
        ekatte_csv.next()   # skip the header
        ekatte_dict = {}
        # array of settlement names
        ekatte_locations = []

        for row in ekatte_csv:
            cleaned_loc = nowhitespaces.sub("", row[2].decode('utf-8')).lower()
            set_type = row[1].decode('utf-8')  # settlement type
            nuts3 = row[3]
            nuts4 = row[4]
            ekatte_locations.append(cleaned_loc)
            if cleaned_loc in ekatte_dict:
                if set_type in ekatte_dict[cleaned_loc]:
                    ekatte_dict[cleaned_loc][set_type].append((nuts3, nuts4))
                else:
                        ekatte_dict[cleaned_loc][set_type] = [(nuts3, nuts4)]
            else:
                ekatte_dict[cleaned_loc] = dict({set_type: [(nuts3, nuts4)]})

        ekatte_file.close()
        return (ekatte_dict, ekatte_locations)

    def read_provinces(self):
        """Reads the provinces csv file with mapping between province name and
           province nuts3 code

        Args:
            filename (str): The filename of the csv file

        Returns:
            A tuple of dict and array. The array contains the all provinces

            The dictionary has the following format:
                {key: province name
                 value: province nuts3 code}
        """
        try:
            province_file = open(self.f_provinces, 'r')
        except IOError as e:
            logging.error("%s", e)
            return (None, None)

        province_csv = csv.reader(province_file, delimiter=';')

        # key: province name
        # value: nuts3 code
        provinces_dict = {}
        # array of province names
        provinces = []
        for row in province_csv:
            for splitted in row[0].decode('utf-8').split('/'):
                cleaned_province = nowhitespaces.sub("", splitted.lower())
                provinces.append(cleaned_province)
                provinces_dict[cleaned_province] = row[1]

        province_file.close()
        return (provinces_dict, provinces)

    def classify_job_location(self, **kwargs):

        """The main workhorse of this class
        """
        # some constants and misc stuff
        BULGARIA = 'българия'.decode('utf-8')
        CITY = 'гр.'.decode('utf-8')
        OBLAST = 'област'.decode('utf-8')
        UNNAMED = "unnamed"

        def remove_artifacts(loc):
            artifacts = ["с.", "гр.", "село", "град"]
            for a in artifacts:
                loc = loc.replace(a.decode("utf-8"), "")
            return loc

        return_codes = (None, None)  # (nuts3, nuts4)
        #
        job_posting_url = kwargs.pop("job_url", None)
        location = kwargs.pop("location", None)
        location2 = kwargs.pop("location2", None)
        if not (job_posting_url and location and location2):
            self.logger.error("Inadequate kwargs")
            return return_codes
        # for some reason some entries for Обзор have a 'O'
        # instead of the unicode code for the cyrrilic 'O' u'\u041e'
        # probably the issue comes from the web crawler (TODO: look into it)
        # here, we simply replace the 'O' with the proper unicode char.
        location = location.replace('O', u'\u041e').lower()
        location = nowhitespaces.sub("", location)
        location = remove_artifacts(location)
        location2 = location2.lower()
        location2_bulgaria = False
        if location2 == BULGARIA:
            location2_bulgaria = True

        # Check if location2 is the name of a province from provinces.csv
        location2_splitted = location2.split(OBLAST, 1)
        location2_resolved = False
        if len(location2_splitted) == 2:
            # e.g. location2 = 'област велико търново'
            #      location2_splitted = ['', 'вeliko търново']
            location2_cleaned = nowhitespaces.sub("", location2_splitted[1])
            if location2_cleaned in self.provinces:
                location2_resolved = True

        # note location2_resolved==True and location2_bulgaria==True is
        # not possible sice 'българия' is not defined as a province in
        # provinces.csv

        # try to find the settlement from 'location' in the EKATTE data
        match_list = [place == location for place in self.ekatte_locations]

        # get the indeces of the matches
        found = list(compress(xrange(len(match_list)), match_list))

        if len(found) == 1:
            ekatte_loc = self.ekatte_locations[found[0]]
            set_type_dict = self.ekatte_dict[ekatte_loc]
            # sanity check, len(found)= 1 =len(settlement_type_dict.keys())
            if len(set_type_dict.keys()) != 1:
                self.logger.error(("Inconsistent settlement types "
                                   "for settlement %s"), ekatte_loc)
                return return_codes
            #
            nuts3 = set_type_dict[set_type_dict.keys()[0]][0][0]
            nuts4 = set_type_dict[set_type_dict.keys()[0]][0][1]
            # check for mismatch between EKATTE nuts3 and 'location2'
            if location2_resolved:
                nuts3_sqlite = self.provinces_dict[location2_cleaned]
                if (nuts3_sqlite != nuts3):
                    self.logger.debug(("location2 nuts3 %s does not "
                                       "match EKATTE nuts3 %s for job %s. "
                                       "Preferring EKATTE nuts3"),
                                      nuts3_sqlite, nuts3, job_posting_url)
                # nuts3=nuts3_sqlite

            # add the job posting in its corresponding georgaphical 'bucket'
            return_codes = (nuts3, nuts4)

        # no settlement with name 'location' has been found in the
        # EKATTE data. Let's hope that location2 has been resolved
        elif len(found) == 0:
            if location2_resolved:
                nuts3 = self.provinces_dict[location2_cleaned]
                return_codes = (nuts3, UNNAMED)
            else:
                self.logger.info(("Cannot find location %s and resolve "
                                  "location %s for job %s"),
                                 location, location2, job_posting_url)

        # multiple matches exist in the EKATTE data for
        # the settlement in 'location'
        elif len(found) > 1:
            # use location2 to differentiate
            if location2_resolved:
                '''
                Тhe entry is e.g. с. Габрово област Благоевград
                The EKATTE data for Габрово is:
                    с.,Габрово,BLG,BLG03
                    гр.,Габрово,GAB,GAB05
                    с.,Габрово,KRZ,KRZ35
                '''
                nuts3 = self.provinces_dict[location2_cleaned]
                ekatte_loc = self.ekatte_locations[found[0]]
                settlement_type_dict = self.ekatte_dict[ekatte_loc]
                _found = False
                nuts4 = UNNAMED
                for types in settlement_type_dict:
                    nuts_codes = settlement_type_dict[types]
                    for nuts in nuts_codes:
                        if nuts[0] == nuts3:
                            nuts4 = nuts[1]
                            _found = True
                            break
                    if _found:
                        break

                # add the job posting to the proper bucket
                return_codes = (nuts3, nuts4)

            # location2 not resolved,
            # try to find a type CITY settlement with a name 'location'
            else:
                '''
                Тhe entry is e.g. Габрово/България

                The EKATTE data for Габрово is:
                    с.,Габрово,BLG,BLG03
                    гр.,Габрово,GAB,GAB05
                    с.,Габрово,KRZ,KRZ35

                If location2 is simply 'българия' then always assume that
                'location' is a city.
                '''
                if location2_bulgaria:
                    ekatte_loc = self.ekatte_locations[found[0]]
                    settlmnt_type_dict = self.ekatte_dict[ekatte_loc]
                    if CITY in settlmnt_type_dict:
                        nuts_codes = settlmnt_type_dict[CITY]
                        if len(nuts_codes) > 1:
                            self.logger.info(("More than 1 cities exist for "
                                              "location %s. Without location2 "
                                              "cannot resolve for job %s"),
                                             location, job_posting_url)
                        else:
                            nuts3 = nuts_codes[0][0]
                            nuts4 = nuts_codes[0][1]
                            return_codes = (nuts3, nuts4)
                    # no cities exist with the name 'location'
                    else:
                        self.logger.info(("Cannot resolve location %s to a "
                                          "main city in the absense of "
                                          "location2 for job %s"),
                                         location, job_posting_url)
                # giving up on this job, nothing can be done
                else:
                    self. logger.info(("location2 (%s) and location (%s) "
                                       " cannot be resolved for job %s. "
                                       "Giving up."),
                                      location2, location, job_posting_url)
        # end if len(found) == 1
        self.logger.debug("%s / %s categorized as %s / %s for job %s",
                          location, location2,
                          return_codes[0], return_codes[1], job_posting_url)
        return return_codes
