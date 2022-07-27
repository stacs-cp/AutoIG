import os
import json
import argparse

import sys

scriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(scriptDir)

import utils


def convert_essence_instance_to_mzn(
    generatorFile, essenceParamFile, outputMznFile="default"
):
    """
    convert an essence param file to minizinc format
    inputs:
        - generatorFile: we need to read this file to recognise the type of each instance param
    """
    # TODO: implement this function (this function can be done automatically, at least for minizinc competition's problems)

    if outputMznFile == "default":
        # TODO: maybe fix this. what if there is no .param extension?
        outputMznFile = essenceParamFile.replace(".param", ".dzn")

    ### this is just a temporary implementation while waiting for Oz to implement the translation in conjure

    # get problem name
    with open(generatorFile, "rt") as f:
        ls = [s[:-1] for s in f.readlines()]
        problem = ls[0].replace("$", "").strip()

    assert problem in [
        "macc",
        "carpet-cutting",
        "racp",
        "mario",
        "pillars-and-planks",
        "lot-sizing",
    ]

    if problem == "macc":
        macc_essence_to_mzn(essenceParamFile, outputMznFile)

    if problem == "carpet-cutting":
        carpet_cutting_essence_to_mzn(essenceParamFile, outputMznFile)

    if problem == "mario":
        mario_essence_to_mzn(essenceParamFile, outputMznFile)

    if problem == "racp":
        racp_essence_to_mzn(essenceParamFile, outputMznFile)

    if problem == "pillars-and-planks":
        pillars_essence_to_mzn(essenceParamFile, outputMznFile)

    if problem == "lot-sizing":
        lot_sizing_essence_to_mzn(essenceParamFile, outputMznFile)


def _dict_to_array(jsondict):
    """
    Helper function to translate an array represented as a dict to a python list.
    i.e., turn this { "1": 1, "2": 1, "3": 1 } into this [1,1,1].
    """
    assert type(jsondict) is dict

    newlist = []

    keys = [int(k) for k in jsondict.keys()]
    keys.sort()

    for key in keys:
        newlist.append(jsondict[str(key)])

    return newlist


def lot_sizing_essence_to_mzn(essenceParamFile, outputMznFile):
    """
    Translates a mario instance in essence to a mario instance in dzn
    """
    cmd = "conjure pretty --output-format=json " + essenceParamFile
    output, _ = utils.run_cmd(cmd, printOutput=False)
    s = "".join(output.split("\n")[1:])
    data = json.loads(s)
    # DEBUG print(json.dumps(data, indent=4))

    with open(outputMznFile, "wt") as f:
        for key, value in data.items():
            # We ignore Auxiliary variables
            if key.startswith("Aux"):
                continue
            # directly output all ints
            elif type(value) is int:
                print(f"{key} = {value};", file=f)
                # print(f"{key} = {value};")
            # conso is a matrix of integers
            elif key == "change_cost":
                str_contents = ""
                listofrows = _dict_to_array(value)
                for row in listofrows:
                    str_contents += (
                        "| " + ", ".join(str(x) for x in _dict_to_array(row)) + "\n"
                    )
                print(f"{key} = array2d(Orders0,Orders0, [{str_contents}|]);", file=f)
                # print(f"{key} = array2d(Orders0,Orders0, [{str_contents}|]);")
            # goldInHouse is an array of integers
            elif key == "item_type":
                listofints = _dict_to_array(value)
                content = ", ".join(str(x) for x in listofints)
                print(f"{key} = array1d(Orders0, [{content}]);", file=f)
                # print(f"{key} = array1d(Orders0, [{content}]);")
            elif key == "due_period" or key == "item_type" or key == "nb_of_orders":
                listofints = _dict_to_array(value)
                content = ", ".join(str(x) for x in listofints)
                print(f"{key} = [{content}];", file=f)
                # print(f"{key} = [{content}];")
            else:
                assert False


def mario_essence_to_mzn(essenceParamFile, outputMznFile):
    """
    Translates a mario instance in essence to a mario instance in dzn
    """
    cmd = "conjure pretty --output-format=json " + essenceParamFile
    output, _ = utils.run_cmd(cmd, printOutput=False)
    s = "".join(output.split("\n")[1:])
    data = json.loads(s)
    # DEBUG print(json.dumps(data, indent=4))

    with open(outputMznFile, "wt") as f:
        for key, value in data.items():
            # We ignore Auxiliary variables
            if key.startswith("Aux"):
                continue
            # directly output all ints
            elif type(value) is int:
                print(f"{key} = {value};", file=f)
                # print(f"{key} = {value};")
            # conso is a matrix of integers
            elif key == "conso":
                str_contents = ""
                listofrows = _dict_to_array(value)
                for row in listofrows:
                    str_contents += (
                        "| " + ", ".join(str(x) for x in _dict_to_array(row)) + "\n"
                    )
                print(f"{key} = [{str_contents}|];", file=f)
                # print(f"{key} = [{str_contents}|];")
            # goldInHouse is an array of integers
            elif key == "goldInHouse":
                listofints = _dict_to_array(value)
                content = ", ".join(str(x) for x in listofints)
                print(f"{key} = [{content}];", file=f)
                # print(f"{key} = [{content}];")
            else:
                assert False


def carpet_cutting_essence_to_mzn(essenceParamFile, outputMznFile):
    """
    Translates a carpet_cutting instance in essence to a carpet_cutting instance in dzn
    """
    cmd = "conjure pretty --output-format=json " + essenceParamFile
    output, _ = utils.run_cmd(cmd, printOutput=False)
    s = "".join(output.split("\n")[1:])
    data = json.loads(s)
    # DEBUG print(json.dumps(data, indent=4))

    with open(outputMznFile, "wt") as f:
        for key, value in data.items():
            # We ignore Auxiliary variables
            if key.startswith("Aux"):
                continue
            # directly output all ints
            elif type(value) is int:
                print(f"{key} = {value};", file=f)

            # rm_rec_ids and rm_ori are list of sets in the dzn.
            # In the JSON from conjure those are a dict of arrays of ints.
            elif key == "rm_rec_ids" or key == "rm_ori":
                listofsets = _dict_to_array(value)
                # turn every "set" into a str representation
                for i in range(0, len(listofsets)):
                    listofsets[i] = "{" + ", ".join(str(x) for x in listofsets[i]) + "}"
                print(f"{key} = [{', '.join(listofsets)}];", file=f)

            # Those two are matrices of integers.
            elif key == "rm_rec_os_x" or key == "rm_rec_os_y":
                str_contents = ""
                listofrows = _dict_to_array(value)
                for row in listofrows:
                    str_contents += (
                        "| " + ", ".join(str(x) for x in _dict_to_array(row)) + "\n"
                    )
                print(f"{key} = [{str_contents}|];", file=f)

            # now only arrays of ints are left now
            else:
                listofints = _dict_to_array(value)
                content = ", ".join(str(x) for x in listofints)
                print(f"{key} = [{content}];", file=f)


def macc_essence_to_mzn(essenceParamFile, outputMznFile):
    """
    Translates a MACC instance in essence to a MACC instance in dzn
    """
    cmd = "conjure pretty --output-format=json " + essenceParamFile
    output, _ = utils.run_cmd(cmd, printOutput=False)
    s = "".join(output.split("\n")[1:])
    data = json.loads(s)
    mznContent = []
    for name in data:
        if name == "building":
            continue
        mznContent.append(name + " = " + str(data[name]) + ";")
    building = "building = array2d(YY,XX,[\n"
    for x in range(data["X"]):
        r = data["building"][str(x)]
        building += ",".join([str(r[str(y)]) for y in range(data["Y"])])
        building += ",\n"
    building += "]);"
    mznContent.append(building)
    with open(outputMznFile, "wt") as f:
        f.write("\n".join(mznContent))


def racp_essence_to_mzn(essenceParamFile, outputMznFile):
    """
    Translates an RACP instance, or crashes.
    """
    cmd = "conjure pretty --output-format=json " + essenceParamFile
    output, _ = utils.run_cmd(cmd, printOutput=False)
    s = "".join(output.split("\n")[1:])
    data = json.loads(s)
    mznContent = []

    #  Numerical params
    for name in ["n_res", "t_max", "n_tasks"]:
        mznContent.append(name + " = " + str(data[name]) + ";")

    # unit cost of resource
    costarray = [data["cost"][str(i)] for i in range(1, data["n_res"] + 1)]
    mznContent.append("cost = " + str(costarray) + ";")

    # duration
    dur = [data["dur"][str(i)] for i in range(1, data["n_tasks"] + 1)]
    mznContent.append("dur = " + str(dur) + ";")

    # successors
    succ = [
        (
            str(set(data["succ_rel"][str(i)]))
            if len(data["succ_rel"][str(i)]) > 0
            else "{}"
        )
        for i in range(1, data["n_tasks"] + 1)
    ]
    mznContent.append("succ = [" + (", ".join(succ)) + "];")

    rr = [
        [str(data["rr"][str(i)][str(j)]) for j in range(1, data["n_tasks"] + 1)]
        for i in range(1, data["n_res"] + 1)
    ]
    rrjoininner = [",".join(rr[i]) for i in range(data["n_res"])]

    mznContent.append("rr = [|" + (" | ".join(rrjoininner)) + "|];")

    with open(outputMznFile, "wt") as f:
        f.write("\n".join(mznContent))


def sortEssenceArray(xs):
    # sort by key-as-int
    xs_sorted = sorted([(int(i), j) for i, j in xs.items()])
    # drop the keys
    return [j for i, j in xs_sorted]


def pillars_essence_to_mzn(essenceParamFile, outputMznFile):
    cmd = "conjure pretty --output-format=json " + essenceParamFile
    output, _ = utils.run_cmd(cmd, printOutput=False)
    s = "".join(output.split("\n")[1:])
    solution = json.loads(s)

    with open(outputMznFile, "wt") as f:
        print("planks = %s;" % solution["planks"], file=f)
        print(
            "plank_width = %s;"
            % sortEssenceArray(solution["plank_width"])[: int(solution["planks"])],
            file=f,
        )
        print("pillars = %s;" % solution["pillars"], file=f)
        print(
            "pillar_height = %s;"
            % sortEssenceArray(solution["pillar_height"])[: int(solution["pillars"])],
            file=f,
        )
        print(
            "pillar_width = %s;"
            % sortEssenceArray(solution["pillar_width"])[: int(solution["pillars"])],
            file=f,
        )
        print("available_width= %s;" % solution["available_width"], file=f)
        print("available_height= %s;" % solution["available_height"], file=f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Set up a tuning experiment for automated instance generation"
    )

    # general settings
    parser.add_argument(
        "--generatorFile",
        required=True,
        type=str,
        help="Generator File (to read the types)",
    )
    parser.add_argument(
        "--essenceParamFile",
        required=True,
        type=str,
        help="Essence param file to convert",
    )
    parser.add_argument(
        "--outDznFile", default="default", type=str, help="Output .dzn file"
    )

    # read from command line args
    args = parser.parse_args()

    # run the "main"
    convert_essence_instance_to_mzn(
        args.generatorFile, args.essenceParamFile, args.outDznFile
    )
