import json
from math import sqrt
import sys
import os
from utils import run_cmd, run_cmd_with_timeout, log, delete_file
import pandas as pd

# Define constants for outputs
detailedOutputDir = "./detailed-output"

# what will be needed for framework:
# instance parameter file
# solver flags (may include time limit)
# will need to implement solver time limit by user
# memory limit implementation
# seed in case of nondeterminism
def call_solve_sat_mapf(instFile, solverPath, solverFlags="-e at_parallel_soc_all", solverTimeLimit=60, solverMemLimit=8192, seed=None):
    params = read_shelfworld_inst_params(instFile=instFile)
    grid = draw_map_shelfworld(params["n_shelves_col"], params["n_shelves_row"], params["shelf_col_size"], params["shelf_row_size"], params["corridor_size"], params["buffer_col"], params["buffer_row"])
    write_map_file(instFile, grid)
    
    bots_start, bots_end = get_bots(params)
    n_col, n_row = get_side_lengths(params)

    instance = os.path.basename(instFile).replace(".param", "")
    scenfile = os.path.join(detailedOutputDir, instance + ".scen")
    outfile = os.path.join(detailedOutputDir, instance + "-sat-mapf.out")

    write_scen_file(instfile=instFile, scenfile=scenfile, bots_start=bots_start, bots_end=bots_end, n_col=n_col, n_row=n_row)
    
    use_runsolver = sys.platform.startswith("linux")

    # define runsolver temp file name
    runsolver_tmp_file = os.path.join(detailedOutputDir, instance + ".runsolver")
    runsolver_tmp_solver_outfile = os.path.join(detailedOutputDir, instance + ".satsolver.out")

    cnf_tmp_file = os.path.join(detailedOutputDir, instance + ".cnf")

    # delay btwn SIGTERM and SIGKILL when timeout in runsolver, to give solver time to gracefully exit
    runsolver_delay = 2

    cmd = f"{solverPath} -s {scenfile} -m {detailedOutputDir} -l 2 -f {outfile} {solverFlags} -c {cnf_tmp_file}"
    
    if use_runsolver:
        cmd = (
            f"runsolver -d {runsolver_delay} --wall-clock-limit {solverTimeLimit} --vsize-limit {solverMemLimit} " +
            cmd + f" > {runsolver_tmp_solver_outfile}"
        )

    log("Running command:" + cmd)

    output, returncode = run_cmd(cmd)

    status = "sat"

    delete_file([cnf_tmp_file])
    # log(output)

    if use_runsolver:
        memTaken = 0
        memMax = 0
            # with open(runsolver_tmp_file) as f:
        for index, line in enumerate(output.splitlines()):
            # check if minion times out or exceeds set memory
            if "Maximum wall clock time exceeded" in line:
                returnCode = 0
                status = "solverTimeOut"
                break
            elif "Maximum VSize exceeded" in line or "std::bad_alloc" in line:
                returnCode = 0
                status = "solverMemOut"
                break
            elif "Child status" in line:
                returnCode = int(line.split(":")[1].strip())
                # Check if minion return code is error
                if returnCode != 0:
                    raise Exception(f"Sat solver exited with error code {returnCode}")
            
            elif "Max. virtual memory (cumulated for all children) (KiB):" in line:
                memTaken = int(line.split(":")[1].strip())
        if memTaken >= solverMemLimit * 1024: # convert to KiB from MiB
            returnCode = 0
            status = "solverMemOut"
            
                        
    time = 0.0

    with open(os.path.join(detailedOutputDir, instance + ".runsolver.out"), "w") as runsolverFile:
        runsolverFile.write(output)

    # TODO deal with crashes etc.
    if status == "sat":
        with open(outfile, "r") as f:
            for line in f.readlines():
                if "CNF building time" in line:
                    time += float(line.replace("CNF building time:", "").strip())
                elif "SAT solving time" in line:
                    time += float(line.replace("SAT solving time:", "").strip())
                    
    return status, time / 1000.0 # time is given in ms


def call_solve_CBSH2(instFile, solverPath, solverFlags="", solverTimeLimit=60, solverMemLimit=8192, seed=None):
    params = read_shelfworld_inst_params(instFile=instFile)
    grid = draw_map_shelfworld(params["n_shelves_col"], params["n_shelves_row"], params["shelf_col_size"], params["shelf_row_size"], params["corridor_size"], params["buffer_col"], params["buffer_row"])
    write_map_file(instFile, grid)
    
    bots_start, bots_end = get_bots(params)
    n_col, n_row = get_side_lengths(params)

    instance = os.path.basename(instFile).replace(".param", "")
    scenfile = os.path.join(detailedOutputDir, instance + ".scen")
    outfile = os.path.join(detailedOutputDir, instance + "-cbs-mapf.csv")

    write_scen_file(instfile=instFile, scenfile=scenfile, bots_start=bots_start, bots_end=bots_end, n_col=n_col, n_row=n_row)
    
    use_runsolver = sys.platform.startswith("linux")

    # delay btwn SIGTERM and SIGKILL when timeout in runsolver, to give solver time to gracefully exit
    runsolver_delay = 2

    runsolver_tmp_solver_outfile = os.path.join(detailedOutputDir, instance + ".cbssolver.out")


    cmd = f"{solverPath} -a {scenfile} -m {os.path.join(detailedOutputDir, instance+".map")} -o {outfile} -k {len(bots_start)} {solverFlags}"
    
    if use_runsolver:
        cmd = (
            f"runsolver -d {runsolver_delay} --wall-clock-limit {solverTimeLimit} --vsize-limit {solverMemLimit} " +
            cmd + f" > {runsolver_tmp_solver_outfile}"
        )

    log("Running command:" + cmd)

    output, returncode = run_cmd(cmd)
    status = "sat"

    if use_runsolver:
        memTaken = 0
        memMax = 0
            # with open(runsolver_tmp_file) as f:
        for index, line in enumerate(output.splitlines()):
            # check if minion times out or exceeds set memory
            if "Maximum wall clock time exceeded" in line:
                returnCode = 0
                status = "solverTimeOut"
                break
            elif "Maximum VSize exceeded" in line or "std::bad_alloc" in line:
                returnCode = 0
                status = "solverMemOut"
                break
            elif "Child status" in line:
                returnCode = int(line.split(":")[1].strip())
                # Check if minion return code is error
                if returnCode != 0:
                    raise Exception(f"cbs solver exited with error code {returnCode}")
            elif "Max. virtual memory (cumulated for all children) (KiB):" in line:
                memTaken = int(line.split(":")[1].strip())
            elif "Max. memory (cumulated for all children) (KiB):" in line:
                memMax = int(line.split(":")[1].strip())
        if memTaken >= solverMemLimit * 1024: # convert to KiB from MiB:
            returnCode = 0
            status = "solverMemOut"
                        
    time = 0.0

    # TODO deal with crashes etc.
    if status == "sat":
        df = pd.read_csv(outfile)

        time = float(df["runtime"][0])
                    
    return status, time

def call_solve_cbs_mapf(instFile, solverPath, solverFlags="disjoint --hlsolver ICBS", solverTimeLimit=60, solverMemLimit=8192,seed=None):
    cbs_param_file = detailedOutputDir + "/" + os.path.basename(instFile).replace(".param", ".txt")
    write_cbs_file(instFile, cbs_param_file)
    
    outfile = os.path.join(detailedOutputDir, os.path.basename(instFile).replace(".param", "") + "-cbs.out")

    use_runsolver = sys.platform.startswith("linux")

    instance = os.path.basename(instFile).replace(".param", "")
    # define runsolver temp file name
    runsolver_tmp_file = os.path.join(detailedOutputDir, instance + ".runsolver")
    # runsolver_tmp_solver_outfile = instance + ".satsolver.out"

    # delay btwn SIGTERM and SIGKILL when timeout in runsolver, to give solver time to gracefully exit
    runsolver_delay = 2

    cmd = f"python3 {solverPath} --instance \"{cbs_param_file}\" {solverFlags}"

    if use_runsolver:
        cmd = (
            f"runsolver -o {outfile} -d {runsolver_delay} --wall-clock-limit {solverTimeLimit} --vsize-limit {solverMemLimit} " +
            cmd
        )

    status = "sat"
    time=0.0

    log("Running command:" + cmd)

    # TODO deal with crashes, write output to file.
    cmdOutput, returnCode = run_cmd(cmd)

    if use_runsolver:
        # with open(runsolver_tmp_file) as f:
            for index, line in enumerate(cmdOutput.splitlines()):
                # check if minion times out or exceeds set memory
                if "Maximum wall clock time exceeded" in line:
                    returnCode = 0
                    status = "solverTimeOut"
                    break
                elif "Maximum VSize exceeded" in line:
                    returnCode = 0
                    status = "solverMemOut"
                    break
                elif "Child status" in line:
                    returnCode = int(line.split(":")[1].strip())
                    # Check if minion return code is error
                    if returnCode != 0:
                        raise Exception(f"Sat solver exited with error code {returnCode}")

    with open(outfile) as output:
        for line in output.readlines():
            if "CPU time" in line:
                time = float(line.replace("CPU time (s):    ", ""))
    
    # with open(outfile, "w") as f:
        # f.write(cmdOutput)
    if status == "solverTimeOut":
        return "solverTimeOut", solverTimeLimit
    return status, time

def write_cbs_file(instFile, cbs_param_file):
    params = read_shelfworld_inst_params(instFile)
    grid = draw_map_shelfworld(params["n_shelves_col"], params["n_shelves_row"], params["shelf_col_size"], params["shelf_row_size"], params["corridor_size"], params["buffer_col"], params["buffer_row"])
    n_col, n_row = get_side_lengths(params)
    bots_start, bots_end = get_bots(params)
    
    if not os.path.isfile(cbs_param_file):
        with open(cbs_param_file, "a") as f:
            f.write(f"{n_row} {n_col}\n")
            
            for y in grid:
                for x in y:
                    f.write(x)
                f.write("\n")
            f.write(str(len(bots_start))+"\n")
            
            for i in range(len(bots_start)):
                col_start = bots_start[i] % n_col
                row_start = bots_start[i] // n_col
                col_end = bots_end[i] % n_col
                row_end = bots_end[i] // n_col

                print(f"Bot {i} {bots_start[i]} {bots_end[i]}: start ({row_start}, {col_start}) -> end ({row_end}, {col_end})")

                f.write(f"{row_start} {col_start} {row_end} {col_end}\n")
    
    return

def get_bots(params):
    bots_start = []
    bots_end = []
    for bot in params["bot_start"]:
        bots_start.append(params["bot_start"][bot])
    for bot in params["bot_end"]:
        bots_end.append(params["bot_end"][bot])
    return bots_start, bots_end

def get_side_lengths(params):
    col_l = params["n_shelves_col"] * (params["shelf_col_size"] + params["corridor_size"]) + 2 * params["buffer_col"]
    row_l = params["n_shelves_row"] * (params["shelf_row_size"] + params["corridor_size"]) + 2 * params["buffer_row"]
    return col_l, row_l

def is_shelf(pos, n_shelves_col, n_shelves_row, shelf_col_size, shelf_row_size, corridor_size, buffer_col, buffer_row):
    col_l = n_shelves_col * (shelf_col_size + corridor_size) + 2 * buffer_col
    row_l = n_shelves_row * (shelf_row_size + corridor_size) + 2 * buffer_row
	
    pos_col = pos % col_l
    pos_row = pos // col_l

    x = (
        buffer_col <= pos_col
        and pos_col < col_l - buffer_col

        and buffer_row <= pos_row
        and pos_row < row_l - buffer_row
        
        and (pos_col - buffer_col) % (shelf_col_size + corridor_size) < shelf_col_size 
        and (pos_row - buffer_row) % (shelf_row_size + corridor_size) < shelf_row_size
        )

    # print("pos", pos, (pos_x - buffer_l))
    
    return x
		
def draw_map_shelfworld(n_shelves_col, n_shelves_row, shelf_col_size, shelf_row_size, corridor_size, buffer_col, buffer_row):
    col_l = n_shelves_col * (shelf_col_size + corridor_size) + 2 * buffer_col
    row_l = n_shelves_row * (shelf_row_size + corridor_size) + 2 * buffer_row

    # print("length:", col_l, "width:", row_l)

    grid = [['@' if is_shelf(y * col_l + x,
                              n_shelves_col,
                              n_shelves_row, 
                              shelf_col_size, 
                              shelf_row_size, 
                              corridor_size, 
                              buffer_col, 
                              buffer_row)
                    else '.' for x in range(col_l)] for y in range(row_l)]
    
    # for y in grid:
    #     for x in y:
    #         print(x, end=" ")
    #     print()
    return grid
        
def read_shelfworld_inst_params(instFile:str):
    cmd = f"conjure pretty {instFile} --output-format=json"
    results_dict = run_cmd(cmd)
    try:
        # Removes the first line of "parsing as a parameter file" that is not Json
        parsed_json = json.loads(results_dict[0][results_dict[0].find("\n") + 1:])
    except json.JSONDecodeError as e:
        print("Failed to parse JSON in shelfworld res")
        # exit()
    return parsed_json

# Stops if file with same name already exists
def write_map_file(instFile, map):
    instance = os.path.basename(instFile).replace(".param", "")
    mapfile = os.path.join(detailedOutputDir, instance + ".map")
    if(not os.path.isfile(mapfile)):
        with open(mapfile, "a") as f:
            f.write("type octile\n")
            f.write("height " + str(len(map)) + "\n")
            f.write("width " + str(len(map[0])) + "\n")
            f.write("map\n")
            for y in map:
                for x in y:
                    f.write(x)
                f.write("\n")
    return

def write_scen_file(instfile, scenfile, bots_start, bots_end, n_col, n_row):
    mapfile = os.path.basename(instfile).replace(".param", ".map")
    if(not os.path.isfile(scenfile)):
        with open(scenfile, "a") as f:
            f.write("version 1\n")
            for i in range(len(bots_start)):
                col_start = bots_start[i] % n_col
                row_start = bots_start[i] // n_col
                col_end = bots_end[i] % n_col
                row_end = bots_end[i] // n_col
                distance = sqrt((col_start -  col_end)**2 + (row_start - row_end)**2)
                f.write(f"0\t{mapfile}\t{n_col}\t{n_row}\t{col_start}\t{row_start}\t{col_end}\t{row_end}\t{distance}\n")
    return
