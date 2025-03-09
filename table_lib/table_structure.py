from copy import deepcopy
from .utils import *


class TableStructure:
    def __init__(self, data, overlap_threshold=8, min_dist=3):
        self.data = deepcopy(data)
        self.overlap_threshold = overlap_threshold
        self.min_dist = min_dist
        
        self.build_table()
        self.split_queues(self.rows)
        self.split_queues(self.cols)
    
    def __repr__(self,):
        return f"n_cols: {len(self.cols)}, n_rows: {len(self.rows)}"
        
    def build_table(self):
        self.cells = self.build_cells()
        self.rows = self.build_rows()
        self.cols = self.build_cols()
    
    def split_queues(self, queues):
        new_queues = {}
        for i,q in queues.items():
            sub_queues = q.split_child_queues(self.cells)
            if sub_queues is not None:
                new_queues.update(sub_queues)
        queues.update(new_queues)
        return queues

    def build_cells(self):
        cells = {}
        for c in self.data['annotations']:
            adjs = find_adjacent_polygons(self.data['annotations'], c['id'], 
                                          overlap_threshold=self.overlap_threshold, 
                                          min_dist=self.min_dist)
            cell = Cell(
                id=c['id'], 
                polygon=c['segmentation'][0],
                left=adjs['left'],
                right=adjs['right'],
                top=adjs['top'],
                bottom=adjs['bottom'],
                logic_axis=c['logic_axis'][0]
            )
            cells[c['id']] = cell
        return cells
    
    def build_rows(self):
        rows = {}
        visited_cells_id = set()

        def add_cell_to_row(row_id, current_cell, root_cell):
            row_id = str(row_id)
            rows[row_id][current_cell.id] = current_cell
            visited_cells_id.add(current_cell.id)

            for cell_id in current_cell.right:
                # if cell_id in visited_cells_id:
                #     continue

                next_cell = self.cells[cell_id]
                _, _, top, bottom = get_edges(next_cell.polygon)
                _, _, root_top, root_bottom = get_edges(root_cell.polygon)
                if intervals_overlap(top, bottom, root_top, root_bottom, self.overlap_threshold):
                    add_cell_to_row(row_id, next_cell, root_cell)

        row_id = 0
        for cell_id, cell in self.cells.items():
            if len(cell.left) == 0:
                rows[str(row_id)] = {}
                
                add_cell_to_row(row_id, cell, root_cell=cell)
                rows[str(row_id)] = Queue(str(row_id), cells_id=list(rows[str(row_id)].keys()), 
                                          root=cell, queue_type='row', 
                                          overlap_threshold=self.overlap_threshold)
                row_id += 1
        sorted_rows = sort_queue(rows, direction='top')
        for row_id, row in sorted_rows.items():
            row.assign_queue_id(self.cells)
        return sorted_rows
    
    def build_cols(self):
        cols = {}
        visited_cells_id = set()

        def add_cell_to_col(col_id, current_cell, root_cell):
            col_id = str(col_id)
            cols[col_id][current_cell.id] = current_cell
            visited_cells_id.add(current_cell.id)

            for cell_id in current_cell.bottom:
                # if cell_id in visited_cells_id:
                #     continue

                next_cell = self.cells[cell_id]
                left, right, _, _ = get_edges(next_cell.polygon)
                root_left, root_right, _, _ = get_edges(root_cell.polygon)
                if intervals_overlap(left, right, root_left, root_right, self.overlap_threshold):
                    add_cell_to_col(col_id, next_cell, root_cell)

        col_id = 0
        for cell_id, cell in self.cells.items():
            if len(cell.top) == 0:
                cols[str(col_id)] = {}

                add_cell_to_col(col_id, cell, root_cell=cell)
                cols[str(col_id)] = Queue(str(col_id), cells_id=list(cols[str(col_id)].keys()), 
                                          root=cell, queue_type='col', 
                                          overlap_threshold=self.overlap_threshold)
                col_id += 1
        sorted_cols = sort_queue(cols, direction='left')
        for col_id, col in sorted_cols.items():
            col.assign_queue_id(self.cells)
        return sorted_cols

    def get_col_id(self, cell_id):
        return self.cells[cell_id].cols_id

    def get_row_id(self, cell_id):
        return self.cells[cell_id].rows_id

class Queue:
    def __init__(self, id, cells_id, root, queue_type, header=None, overlap_threshold=8):
        assert queue_type in ['row', 'col'], "queue_type has to be `row` or `col`"

        self.id = id
        self.cells_id = cells_id
        # self.polygon = self.build_polygon(self.cells)
        
        self.root = root
        self.queue_type = queue_type
        self.header = header
        
        self.overlap_threshold = overlap_threshold
    
    def __repr__(self):
        x = f"id: {self.id}, root: {self.root.id}"
        return x
    
    def assign_queue_id(self, cells):
        for cell_id in self.cells_id:
            if self.queue_type == 'row':
                cells[cell_id].rows_id.add(self.id)
            elif self.queue_type == 'col':
                cells[cell_id].cols_id.add(self.id)
    
    def get_adjacents_based_on_type(self, cell):
        if self.queue_type == 'row':
           return cell.right
        elif self.queue_type == 'col':
            return cell.bottom
        return None
    
    def split_child_queues(self, cells):
        root = self.root

        childrens = self.get_adjacents_based_on_type(root)

        if len(childrens) < 2:
            return None
        
        queues_cells = {}

        def add_cell_to_queue(queue_id, current_cell, root_cell):
            queue_id = str(queue_id)
            queues_cells[queue_id][current_cell.id] = current_cell

            childrens = self.get_adjacents_based_on_type(current_cell)

            for cell_id in childrens:
                next_cell = cells[cell_id]
                left, right, top, bottom = get_edges(next_cell.polygon)
                root_left, root_right, root_top, root_bottom = get_edges(root_cell.polygon)
                
                if (
                    (self.queue_type == 'col' and intervals_overlap(left, right, root_left, root_right, 
                                                                    self.overlap_threshold))
                    or
                    (self.queue_type == 'row' and intervals_overlap(top, bottom, root_top, root_bottom, 
                                                                    self.overlap_threshold))
                ):
                    add_cell_to_queue(queue_id, current_cell=next_cell, root_cell=root_cell)

        for i, cell_id in enumerate(childrens):
            new_root = cells[cell_id]
            new_id = f"{self.id}.{i}"
            
            queues_cells[new_id] = {}
            queues_cells[new_id][root.id] = root

            add_cell_to_queue(new_id, current_cell=new_root, root_cell=new_root)
            queues_cells[new_id] = Queue(new_id, cells_id=list(queues_cells[new_id].keys()), 
                                         root=new_root, queue_type=self.queue_type, 
                                         overlap_threshold=self.overlap_threshold)
            
            
        sorted_queues =  sort_queue(queues_cells,
                                    direction='left' if self.queue_type=='col' else 'top',
                                    is_child=True)
        for queue_id, queue in sorted_queues.items():
            queue.assign_queue_id(cells)
        return sorted_queues
        
        

class Cell:
    def __init__(self, id, polygon, 
                 left, right, top, bottom, 
                 text=None, cols_id=None, rows_id=None, is_header=None, logic_axis=[]):
        self.id = id
        self.polygon = polygon
        self.text = text
        self.cols_id = set() if cols_id is None else cols_id
        self.rows_id = set() if rows_id is None else rows_id
        self.is_header = is_header
        self.logic_axis = logic_axis
        
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom

    def __repr__(self):
        x = f"id: {self.id}, cols_id: {self.cols_id}, rows_id: {self.rows_id}"
        return x
        

if __name__ == '__main__':
    import json
    

    with open('/Users/ted/Desktop/bordered_table/data.json', 'rb') as f:
        data = json.load(f)
    
    table = TableStructure(data)
    

    