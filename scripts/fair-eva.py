#!/usr/bin/env python3

"""
# Full example
python3 scripts/fair-eva.py --id cb3f56cd-003c-4262-b5d6-729e0f558958 --plugin epos -r https://ics-c.epos-ip.org/development/k8s-epos-deploy/dt-geo/api/v1 --totals

# EXAMPLES
# EPOS Production API
id = "12b76f8e-d10e-4c5d-a113-4855f6bc3435"
oaibase = "https://www.ics-c.epos-eu.org/api/v1"
repo = "epos"

# EPOS prototype API
oaibase =  'https://ics-c.epos-ip.org/development/k8s-epos-deploy/dt-geo/api/v1'
ide = '46676a31-fa8e-4a4a-a3c0-15d689783a08'

# DIGITAL CSIC
id = "http://hdl.handle.net/10261/157765"
oaibase = "http://digital.csic.es/dspace-oai/request"
repo = "oai-pmh"
"""

import argparse
import json
import logging
import socket
import sys
import time

import requests
from flask_babel import Babel, gettext
from flask_babel import lazy_gettext as _l
from prettytable import PrettyTable

FAIR_PRINCIPLES = ["findable", "accessible", "interoperable", "reusable"]

FAIR_RDA_INDICATORS = {
    "RDA_F1_01M": {
        "id": "RDA-F1-01M",
        "indicator": "Metadata is identified by a persistent identifier",
        "priority": "Essential (***)",
    },
    "RDA_F1_01D": {
        "id": "RDA-F1-01D",
        "indicator": "Data is identified by a persistent identifier",
        "priority": "Essential (***)",
    },
    "RDA_F1_02M": {
        "id": "RDA-F1-02M",
        "indicator": "Metadata is identified by a globally unique identifier",
        "priority": "Essential (***)",
    },
    "RDA_F1_02D": {
        "id": "RDA-F1-02D",
        "indicator": "Data is identified by a persistent identifier",
        "priority": "Essential (***)",
    },
    "RDA_F2_01M": {
        "id": "RDA-F2-01M",
        "indicator": "Rich metadata is provided to allow discovery",
        "priority": "Essential (***)",
    },
    "RDA_F3_01M": {
        "id": "RDA-F3-01M",
        "indicator": "Metadata includes the identifier for the data",
        "priority": "Essential (***)",
    },
    "RDA_F4_01M": {
        "id": "RDA-F4-01M",
        "indicator": "Metadata is offered in such a way that it can be harvested and indexed",
        "priority": "Essential (***)",
    },
    "RDA_A1_01M": {
        "id": "RDA-A1-01M",
        "indicator": "Metadata contains information to enable the user to get access to the data",
        "priority": "Important (**)",
    },
    "RDA_A1_02M": {
        "id": "RDA-A1-02M",
        "indicator": "Metadata can be accessed manually (i.e. with human intervention)",
        "priority": "Essential (***)",
    },
    "RDA_A1_02D": {
        "id": "RDA-A1-02D",
        "indicator": "Data can be accessed manually (i.e. with human intervention)",
        "priority": "Essential (***)",
    },
    "RDA_A1_03M": {
        "id": "RDA-A1-03M",
        "indicator": "Metadata identifier resolves to a metadata record",
        "priority": "Essential (***)",
    },
    "RDA_A1_02D": {
        "id": "RDA-A1-02D",
        "indicator": "Data can be accessed manually (i.e. with human intervention)",
        "priority": "Essential (***)",
    },
    "RDA_A1_03D": {
        "id": "RDA-A1-03D",
        "indicator": "Data identifier resolves to a digital object",
        "priority": "Essential (***)",
    },
    "RDA_A1_04M": {
        "id": "RDA-A1-04M",
        "indicator": "Metadata is accessed through standardised protocol",
        "priority": "Essential (***)",
    },
    "RDA_A1_04D": {
        "id": "RDA-A1-04D",
        "indicator": "Data is accessed through standardised protocol",
        "priority": "Essential (***)",
    },
    "RDA_A1_05D": {
        "id": "RDA-A1-05D",
        "indicator": "Data can be accessed automatically (i.e. by a computer program)",
        "priority": "Important (**)",
    },
    "RDA_A1_1_01M": {
        "id": "RDA-A1.1-01M",
        "indicator": "Metadata is accessible through a free access protocol",
        "priority": "Essential (***)",
    },
    "RDA_A1_1_01D": {
        "id": "RDA-A1.1-01D",
        "indicator": "Data is accessible through a free access protocol",
        "priority": "Important (**)",
    },
    "RDA_A1_2_01D": {
        "id": "RDA-A1.2-01D",
        "indicator": "Data is accessible through an access protocol that supports authentication and authorisation",
        "priority": "Useful (*)",
    },
    "RDA_A2_01M": {
        "id": "RDA-A2-01M",
        "indicator": "Metadata is guaranteed to remain available after data is no longer available",
        "priority": "Essential (***)",
    },
    "RDA_I1_01M": {
        "id": "RDA-I1-01M",
        "indicator": "Metadata uses knowledge representation expressed in standardised format",
        "priority": "Important (**)",
    },
    "RDA_I1_01D": {
        "id": "RDA-I1-01D",
        "indicator": "Data uses knowledge representation expressed in standardised format",
        "priority": "Important (**)",
    },
    "RDA_I1_02M": {
        "id": "RDA-I1-02M",
        "indicator": "Metadata uses machine-understandable knowledge representation",
        "priority": "Important (**)",
    },
    "RDA_I1_02D": {
        "id": "RDA-I1-02D",
        "indicator": "Data uses machine-understandable knowledge representation",
        "priority": "Important (**)",
    },
    "RDA_I2_01M": {
        "id": "RDA-I2-01M",
        "indicator": "Metadata uses FAIR-compliant vocabularies",
        "priority": "Important (**)",
    },
    "RDA_I2_01D": {
        "id": "RDA-I2-01D",
        "indicator": "Data uses FAIR-compliant vocabularies",
        "priority": "Useful (*)",
    },
    "RDA_I3_01M": {
        "id": "RDA-I3-01M",
        "indicator": "Metadata includes references to other metadata",
        "priority": "Important (**)",
    },
    "RDA_I3_01D": {
        "id": "RDA-I3-01D",
        "indicator": "Data includes references to other data",
        "priority": "Useful (*)",
    },
    "RDA_I3_02M": {
        "id": "RDA-I3-02M",
        "indicator": "Metadata includes references to other data",
        "priority": "Important (**)",
    },
    "RDA_I3_02D": {
        "id": "RDA-I3-02D",
        "indicator": "Data includes qualified references to other data",
        "priority": "Useful (*)",
    },
    "RDA_I3_03M": {
        "id": "RDA-I3-03M",
        "indicator": "Metadata includes qualified references to other metadata",
        "priority": "Important (**)",
    },
    "RDA_I3_04M": {
        "id": "RDA-I3-04M",
        "indicator": "Metadata includes qualified references to other data",
        "priority": "Useful (*)",
    },
    "RDA_R1_01M": {
        "id": "RDA-R1-01M",
        "indicator": "Plurality of accurate and relevant attributes are provided to allow reuse",
        "priority": "Essential (***)",
    },
    "RDA_R1_1_01M": {
        "id": "RDA-R1.1-01M",
        "indicator": "Metadata includes information about the licence under which the data can be reused",
        "priority": "Essential (***)",
    },
    "RDA_R1_1_02M": {
        "id": "RDA-R1.1-02M",
        "indicator": "Metadata refers to a standard reuse licence",
        "priority": "Important (**)",
    },
    "RDA_R1_1_03M": {
        "id": "RDA-R1.1-03M",
        "indicator": "Metadata refers to a machine understandable reuse licence",
        "priority": "Important (**)",
    },
    "RDA_R1_2_01M": {
        "id": "RDA-R1.2-01M",
        "indicator": "Metadata includes provenance information according to community-specific standards",
        "priority": "Important (**)",
    },
    "RDA_R1_2_02M": {
        "id": "RDA-R1.2-02M",
        "indicator": "Metadata includes provenance information according to a cross-community language",
        "priority": "Useful (*)",
    },
    "RDA_R1_3_01M": {
        "id": "RDA-R1.3-01M",
        "indicator": "Metadata complies with a community standard",
        "priority": "Essential (***)",
    },
    "RDA_R1_3_01D": {
        "id": "RDA-R1.3-01D",
        "indicator": "Data complies with a community standard",
        "priority": "Essential (***)",
    },
    "RDA_R1_3_02M": {
        "id": "RDA-R1.3-02M",
        "indicator": "Metadata is expressed in compliance with a machine-understandable community standard",
        "priority": "Essential (***)",
    },
    "RDA_R1_3_02D": {
        "id": "RDA-R1.3-02D",
        "indicator": "Data is expressed in compliance with a machine-understandable community standard",
        "priority": "Important (**)",
    },
}


class Formatter(logging.Formatter):
    def format(self, record):
        if record.levelno == logging.INFO:
            self._style._fmt = "%(message)s"
        else:
            self._style._fmt = "%(levelname)s: %(message)s"
        return super().format(record)


def get_input_args():
    parser = argparse.ArgumentParser(
        description=("Command-line interface for FAIR EVA tool")
    )
    parser.add_argument(
        "-d",
        "--debug",
        help="Enable debugging",
        action="store_const",
        dest="log_level",
        const=logging.DEBUG,
        default=logging.INFO,
    )
    parser.add_argument(
        "-i",
        "--id",
        metavar="IDENTIFIER",
        type=str,
        help="Identifier of the (meta)data",
    )
    parser.add_argument(
        "-p", "--plugin", metavar="PLUGIN", type=str, help="FAIR EVA plugin name"
    )
    parser.add_argument(
        "-r",
        "--repository",
        metavar="URL",
        type=str,
        help="(meta)data repository endpoint",
    )
    parser.add_argument(
        "--api-endpoint",
        metavar="URL",
        type=str,
        default="http://localhost:9090/v1.0/rda/rda_all",
        help=(
            "Endpoint to perform HTTP request. Example: "
            "http://localhost:9090/v1.0/rda/rda_all"
        ),
    )
    parser.add_argument(
        "-j",
        "--json",
        action="store_true",
        help=("Flag to print the results in JSON format"),
    )
    parser.add_argument(
        "--totals",
        action="store_true",
        help=(" print the totals in each FAIR category"),
    )
    parser.add_argument(
        "--logs",
        action="store_true",
        help=("Prints logs related to the evaluation steps being carried out"),
    )
    parser.add_argument("-s", "--search", type=str, help="data asset to look for")
    parser.add_argument(
        "--store-feather",
        action="store_true",
        help=("Store FAIR results as (fast on-disk) Feather format"),
    )
    parser.add_argument(
        "--store-csv",
        action="store_true",
        help=("Store FAIR results as CSV format"),
    )

    return parser.parse_args()


def is_port_open():
    is_port_open = False
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(("127.0.0.1", 9090))
    if result == 0:
        is_port_open = True
    sock.close()

    return is_port_open


def calcpoints(result):
    keys = FAIR_PRINCIPLES + ["total"]
    values = [0, 0, 0, 0, 0]
    result_points = 0
    weight_of_tests = 0
    points = dict(zip(keys, values))

    for key in keys[:-1]:
        g_weight = 0
        g_points = 0
        for kk in result[key]:
            result[key][kk]["indicator"] = gettext(
                "%s.indicator" % result[key][kk]["name"]
            )

            result[key][kk]["name_smart"] = gettext("%s" % result[key][kk]["name"])

            weight = result[key][kk]["score"]["weight"]
            weight_of_tests += weight
            g_weight += weight
            result_points += result[key][kk]["points"] * weight
            g_points += result[key][kk]["points"] * weight

        points[key] = round((g_points / g_weight), 3)
    points["total"] = round((result_points / weight_of_tests), 2)

    return points


def format_msg_for_table(message_data):
    output_message = "Not available"
    # FIXME Check to overcome issue: https://github.com/EOSC-synergy/FAIR_eva/issues/188
    if isinstance(message_data, str):
        output_message = message_data
    elif isinstance(message_data, dict):
        output_message = str(message_data)
    else:
        if len(message_data) > 0:
            # FIXME Overcome same issue as above: https://github.com/EOSC-synergy/FAIR_eva/issues/188
            if isinstance(message_data[0], str):
                output_message = "\n".join(message_data)
            else:
                if len(message_data) > 1:
                    output_message = "\n".join(
                        [
                            "%s (points: %s)" % (item["message"], item["points"])
                            for item in message_data
                        ]
                    )
                elif len(message_data) == 1:
                    output_message = message_data[0].get("message", "Not available")
    return output_message


def collect_score_data(fair_results):
    # Split by principle: required for setting dividers in the resultant table
    indicators_by_principle = {}
    for principle in FAIR_PRINCIPLES:
        principle_result = fair_results[principle]
        indicators_by_principle[principle] = list(principle_result.values())

    rows = []
    for principle, indicator_list in indicators_by_principle.items():
        for indicator_result in indicator_list:
            # Format output message
            output_message = format_msg_for_table(indicator_result.get("msg", []))
            # Truncate points to two decimals
            points = indicator_result["points"]
            if isinstance(points, float):
                points = "%.2f" % points
            indicator_id_internal = indicator_result["name"].upper()
            indicator_rda_data = FAIR_RDA_INDICATORS[indicator_id_internal]
            row = [
                indicator_rda_data["id"],
                indicator_rda_data["indicator"],
                points,
                output_message,
            ]
            rows.append(row)

    return rows


def print_table(indicator_rows, totals={}):
    table = PrettyTable()
    table.field_names = ["ID", "Indicator", "Score", "Output"]
    table.align = "l"
    table._max_width = {"Indicator": 40, "Output": 60}
    table.add_rows([row for row in indicator_rows])

    # Printing out totals
    if totals:
        # per principle
        table_summary = PrettyTable()
        table_summary.field_names = ["FAIR principle", "Score"]
        table_summary.align = "l"
        # summary_scores = calcpoints(fair_results)
        total_score = totals.pop("total", "NA")
        principle_len = len(totals)
        principle_count = 0
        has_divider = False
        for principle_name, principle_score in totals.items():
            principle_count += 1
            if principle_count == principle_len:
                has_divider = True
            if isinstance(principle_score, float):
                principle_score = "%.2f" % principle_score
            table_summary.add_row(
                [principle_name.capitalize(), principle_score], divider=has_divider
            )
        table_summary.add_row(["Total", total_score])
        print(table_summary)

    # Print indicator table
    print(table)


def search(keytext):
    args = get_input_args()
    max_tries = 5
    headers = {
        "accept": "application/json",
    }
    good = 0
    params = {"facets": "false", "q": keytext}
    if args.plugin in ["epos", "epos_prod"]:
        response = requests.get(
            metadata_endpoint + "/resources/search",
            params=params,
            headers=headers,
        )
        terms = response.json()
        if not terms.get("results", {}):
            logging.error("Could not find results for search query: %s" % params)
            sys.exit(-2)
        number_of_items = len(terms["results"]["distributions"])
        table = PrettyTable()
        table.field_names = [
            "Title",
            "Index",
        ]
        table.align = "l"
        table._max_width = {"Output": 100}
        for index in range((len(terms["results"]["distributions"]))):
            if (index + 1) % 5 == 0:
                div = True
            else:
                div = False
            table.add_row(
                [
                    terms["results"]["distributions"][index]["title"],
                    index,
                ],
                divider=div,
            )
        print(table)
        for j in range(max_tries):
            ind = input(
                "Please choose the index of the item you want to evaluate (from 0 to %s): "
                % str(len(terms["results"]["distributions"]) - 1)
            )
            try:
                if int(ind) > (-1) and int(ind) < number_of_items:
                    good = 1
            except:
                print(
                    "Please introduce an integer between 0 and " + str(number_of_items)
                )
            if good == 1:
                break
        if good == 0:
            print("Max tries, restart program")
            return ()
        global title
        title = terms["results"]["distributions"][int(ind)]["title"]
        return terms["results"]["distributions"][int(ind)]["id"]

    else:
        logging.info(
            "The search function is only availbale for the following plugins: epos"
        )
        sys.exit()


def store(identifier, score_data, file_format="feather", path="/tmp"):
    import os.path

    import pandas as pd

    dframe = pd.DataFrame(score_data)
    dframe.columns = ["fair_indicator", "fair_principle", "score", "message"]
    dframe["score"] = pd.to_numeric(dframe["score"])
    logging.debug("Resultant Pandas data frame: %s" % dframe)

    file_name = "fair_eva_results-%s.%s" % (identifier, file_format)
    file_path = os.path.join(path, file_name)
    if file_format not in ["feather", "csv"]:
        logging.error("Output file format not supported: %s" % file_format)
        sys.exit(-1)
    else:
        logging.debug("Requested %s output format" % file_format)
        if file_format in ["feather"]:
            dframe.to_feather(file_path)
        elif file_format in ["csv"]:
            dframe.to_csv(file_path)

    logging.info("Stored FAIR assessment results to: %s" % file_path)


def main():
    global metadata_endpoint

    # Parse input args
    args = get_input_args()

    # Set different formats for debugging and info
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(Formatter())
    logger.setLevel(args.log_level)
    logger.addHandler(handler)

    url = args.api_endpoint
    if args.repository == None:
        response = requests.get(
            "http://localhost:9090/v1.0/endpoints?plugin=" + args.plugin
        )
        if response.status_code == 404:
            print(
                "Input plugin not found. Look for plugins in the plugins folder. The accepted plugins for this script are: "
                + str(response.json().keys())
            )
            return "Input plugin not found"
        else:
            metadata_endpoint = response.json()

    else:
        metadata_endpoint = args.repository

    is_api_running = False

    for i in range(1, 5):
        if is_port_open():
            logging.debug("FAIR-eva API running on port 9090")
            is_api_running = True
            break
        else:
            logging.debug("FAIR-eva API not running: port 9090 not open")
            logging.debug("Sleeping for 5 seconds..")
            time.sleep(5)
    if not is_api_running:
        logging.error("FAIR-eva API was not able to launch: exiting")
        sys.exit(-1)
    if args.search:
        identifier = search(args.search)
    else:
        identifier = args.id

    headers = {"Content-Type": "application/json"}
    data = {
        "id": identifier,
        "repo": args.plugin,
        "oai_base": metadata_endpoint,
        "lang": "EN",
    }

    if search == True:
        logging.info('Evaluating "' + str(title) + '" with id: ' + identifier)
    else:
        logging.info("Evaluating item with id : " + identifier)

    r = requests.post(url, data=json.dumps(data), headers=headers)
    if not r.ok:
        logging.error("Error returned by FAIR-EVA API: %s" % r.reason)
        logging.debug(r.text)
        sys.exit(r.status_code)
    logging.debug("FAIR results (raw) from FAIR-EVA: %s" % r.json())
    results_all = r.json()
    results = results_all.get(identifier, {})
    logging.debug("FAIR results for (meta)data ID: %s" % results)

    score_results = collect_score_data(results)

    if args.json:
        print(results)
    else:
        totals = {}
        if args.totals:
            totals = calcpoints(results)
        print_table(score_results, totals=totals)
    if args.logs:
        print("\n----- Evaluator logs -----")
        for line in results_all["evaluator_logs"]:
            print(line)

    if args.store_feather:
        store(identifier, score_results)
    if args.store_csv:
        store(identifier, score_results, file_format="csv")


main()
