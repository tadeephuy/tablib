import cv2
from PIL import Image
import numpy as np
from matplotlib import pyplot as plt 
from table_lib.utils import get_edges

offset_y = 50
offset_x = 50

class TableVisualizer():
    def __init__(self, table, image_path, config=None):
        self.table = table
        self.image_path = image_path
        self.config = config
        

    def draw_table(self, show=True):
        image = np.asarray(Image.open(self.image_path))
        image = np.pad(image, pad_width=((offset_y, 0), (offset_x, 0), (0, 0)), 
                    mode='constant', constant_values=255)

        for id,c in self.table.cells.items():
            image = self.draw_cell(id, image, color=(20, 200, 40), shrinkage=4)

        for id,q in self.table.rows.items():
            image = self.draw_queue(id, 'row', image=image, show=False)
        
        for id,q in self.table.cols.items():
            image = self.draw_queue(id, 'col', image=image, show=False)
        
        

        if show:
            plt.imshow(image)
            plt.gcf().set_dpi(500)
            plt.show()
        return image

    def draw_cell(self, cell_id,  image, color=(0,177,255), is_root=False, shrinkage=0):
        cell = self.table.cells[cell_id]
        xs = np.array(cell.polygon[::2]).astype(int) + offset_x
        ys = np.array(cell.polygon[1::2]).astype(int) + offset_y

        coord = []
        for x,y in zip(xs,ys):
            coord.append([x,y])
        coord.append([xs[0],ys[0]])
        
        if not is_root:
            coord[0][0] += shrinkage
            coord[0][1] += shrinkage
            
            coord[1][0] -= shrinkage
            coord[1][1] += shrinkage
            
            coord[2][0] -= shrinkage
            coord[2][1] -= shrinkage
            
            coord[3][0] += shrinkage
            coord[3][1] -= shrinkage
            
            coord[4][0] += shrinkage
            coord[4][1] += shrinkage
        
        image = cv2.polylines(image, [np.array(coord).astype(np.int32)], True, color, 2)
        return image
        
        
    def draw_cell_headers(self, cell_id, show=True):
        image = np.asarray(Image.open(self.image_path))
        image = np.pad(image, pad_width=((offset_y, 0), (offset_x, 0), (0, 0)), 
                    mode='constant', constant_values=255)

        image = self.draw_cell(cell_id, image)
        
        cell = self.table.cells[cell_id]
        
        for id in cell.cols_id:
            col = self.table.cols[id]
            root = col.root
            image = self.draw_cell(root.id, image, color=(255,0,0), is_root=True)
        
        for id in cell.rows_id:
            row = self.table.rows[id]
            root = row.root
            image = self.draw_cell(root.id, image, color=(255,0,0), is_root=True)
        
        if show:
            plt.imshow(image)
            plt.gcf().set_dpi(500)
            plt.show()
        
        return image
        
    
    def draw_queue(self, queue_id, row_or_col, image=None, show=True):
        if image is None:
            image = np.asarray(Image.open(self.image_path))
            image = np.pad(image, pad_width=((offset_y, 0), (offset_x, 0), (0, 0)), 
                        mode='constant', constant_values=255)
        
        queues = self.table.cols if row_or_col == 'col' else self.table.rows

        for cell_id in queues[queue_id].cells_id:
            cell = self.table.cells[cell_id]

            if cell_id == queues[queue_id].root.id:
                color = (255,0,0)
                min_x, max_x, min_y, max_y = get_edges(cell.polygon)
                w = max_x - min_x
                h = max_y - min_y 
                t_x, t_y = min_x + w/2 + offset_x,min_y + h/ 2+ offset_y
                t_x -= 0.3*w
                t_y += 0.1*h
                t_x, t_y = int(t_x), int(t_y)
                
                label = f'{row_or_col[0]}: {queue_id}'
                font = cv2.FONT_HERSHEY_SIMPLEX
                scale = 0.4
                thickness = 1
                (wt, ht), _ = cv2.getTextSize(label,font, scale, thickness)
                if row_or_col == 'col':
                    t_y -= ht
                else:
                    t_y += ht
                
                # Prints the text.    
                image = cv2.rectangle(image, (t_x -5, t_y - ht - 5), (t_x + wt + 5, t_y + 5), 
                                      (230, 230, 230), -1)
                image = cv2.putText(image, label, (t_x,t_y),
                                  font, scale, color, thickness)
                
                image = self.draw_cell(cell_id, image, color=color, is_root=True, shrinkage=4)
                
            else:
                color = (0,70,255)
                image = self.draw_cell(cell_id, image, color=color, is_root=False, shrinkage=4)
        if show:
            plt.imshow(image)
            plt.gcf().set_dpi(500)
            plt.show()
        return image
        
    
    def draw_row(self, row_id):
        return self.draw_queue(row_id, 'row')
    
    def draw_col(self, col_id):
        return self.draw_queue(col_id, 'col')