import json
from math import sqrt
import sys
import os
from utils import run_cmd
import conf

# what will be needed for framework:
# instance parameter file
# solver flags (may include time limit)
# will need to implement solver time limit by user
# seed in case of nondeterminism
def call_solve_sat_mapf(instFile, solverFlags, solverTimelimit, seed):
    params = read_shelfworld_inst_params(instFile=instFile)
    grid = draw_map_shelfworld(params["n_shelves_col"], params["n_shelves_row"], params["shelf_col_size"], params["shelf_row_size"], params["corridor_size"], params["buffer_col"], params["buffer_row"])
    write_map_file(instFile, grid)
    
    bots_start, bots_end = get_bots(params)
    n_col, n_row = get_side_lengths(params)
    write_scen_file(instfile=instFile, bots_start=bots_start, bots_end=bots_end, n_col=n_col, n_row=n_row)
    
    # TODO implement calling the solver
    
    return

def call_solve_cbs_mapf(instFile, solverFlags, solverTimeLimit, seed):
    
    return

def write_cbs_file(instFile):
    params = read_shelfworld_inst_params(instFile)
    grid = draw_map_shelfworld(params["n_shelves_col"], params["n_shelves_row"], params["shelf_col_size"], params["shelf_row_size"], params["corridor_size"], params["buffer_col"], params["buffer_row"])
    n_col, n_row = get_side_lengths(params)
    bots_start, bots_end = get_bots(params)
    
    cbs_param_file = conf.detailedOutputDir + os.path.basename(instFile).replace(".param", ".txt")
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

                f.write(f"{col_start} {row_start} {col_end} {row_end}\n")
    
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

    grid = [['@' if is_shelf(y * col_l + x, n_shelves_col, n_shelves_row, shelf_col_size, shelf_row_size, corridor_size, buffer_col, buffer_row) else '.' for x in range(col_l)] for y in range(row_l)]
    
    # for y in grid:
    #     for x in y:
    #         print(x, end="")
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
        exit()
    return parsed_json

# Stops if file with same name already exists
def write_map_file(instFile, map):
    instance = os.path.basename(instFile).replace(".param", "")
    mapfile = os.path.join(conf.detailedOutputDir, instance + ".map")
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

def write_scen_file(instfile, bots_start, bots_end, n_col, n_row):
    instance = os.path.basename(instfile).replace(".param", "")
    mapfile = instance + ".map"
    scenfile = os.path.join(conf.detailedOutputDir, instance + ".scen")
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