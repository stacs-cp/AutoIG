import json
import sys
import os
from utils import run_cmd

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

    print("length:", col_l, "width:", row_l)

    grid = [['@' if is_shelf(y * col_l + x, n_shelves_col, n_shelves_row, shelf_col_size, shelf_row_size, corridor_size, buffer_col, buffer_row) else '.' for x in range(col_l)] for y in range(row_l)]
    
    for y in grid:
        for x in y:
            print(x, end="")
        print()
        
def read_shelfworld_inst_params(instFile:str):
    cmd = f"conjure pretty {instFile} --output-format=json"
    results_dict = run_cmd(cmd)
    try:
        parsed_json = json.loads(results_dict[0][results_dict[0].find("\n") + 1:])
    except json.JSONDecodeError as e:
        print("Failed to parse JSON in shelfworld res")
        exit()
    return parsed_json

