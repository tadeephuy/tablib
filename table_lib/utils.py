__all__ = ['sort_queue', 'intervals_overlap', 'get_edges', 'find_adjacent_polygons']

def sort_queue(queue_dict, direction, is_child=False):
    # sort queues by their root cells
    assert direction in ['top', 'left'], "direction must be either `top` or `left`"
    if direction == 'top':
        sorted_items = sorted(queue_dict.items(), key = lambda x: x[1].root.polygon[1])
    if direction == 'left':
        sorted_items = sorted(queue_dict.items(), key = lambda x: x[1].root.polygon[0])

    # reindex queue ids
    sorted_queues = {}
    for i, (old_i, q) in enumerate(sorted_items):
        if is_child:
            prefix = '.'.join(old_i.split('.')[:-1])
            q.id = f"{prefix}.{i}"
        else:
            q.id = str(i)
        sorted_queues[q.id] = q
    return sorted_queues

# Function to check if intervals overlap
def intervals_overlap(min1, max1, min2, max2, thresh=1):
    if min2 >= min1 - thresh and max2 <= max1 + thresh:
        return True
    if min1 >= min2 - thresh and max1 <= max2 + thresh:
        return True
    return False

# Function to extract boundaries of a polygon
def get_edges(polygon):
    x_coords = polygon[0::2]
    y_coords = polygon[1::2]
    return min(x_coords), max(x_coords), min(y_coords), max(y_coords)

def find_adjacent_polygons(polygon_list, target_id, overlap_threshold=8, min_dist=3):
    # Find the target polygon
    target_polygon = next((poly for poly in polygon_list if poly['id'] == target_id), None)
    if not target_polygon:
        return None  # If the target polygon isn't found

    target_left, target_right, target_top, target_bottom = get_edges(target_polygon['segmentation'][0])

    closest_right = []
    closest_top = []
    closest_bottom = []
    closest_left = []

    # Iterate over all polygons to find the close enough in each direction
    for poly in polygon_list:
        if poly['id'] != target_id:
            left, right, top, bottom = get_edges(poly['segmentation'][0])

            # Check vertical alignment for left and right adjacency
            if intervals_overlap(target_top, target_bottom, top, bottom, overlap_threshold):
                # Right adjacent
                if left > target_right - overlap_threshold and abs(left - target_right) < min_dist:
                    closest_right.append(poly['id'])
                # Left adjacent
                if right < target_left + overlap_threshold and abs(target_left - right) < min_dist:
                    closest_left.append(poly['id'])

            # Check horizontal alignment for top and bottom adjacency
            if intervals_overlap(target_left, target_right, left, right, overlap_threshold):
                # Bottom adjacent
                if top > target_bottom - overlap_threshold and abs(top - target_bottom) < min_dist:
                    closest_bottom.append(poly['id'])
                # Top adjacent
                if bottom < target_top + overlap_threshold and abs(target_top - bottom) < min_dist:
                    closest_top.append(poly['id'])

    return {
        'right': closest_right,
        'top': closest_top,
        'bottom': closest_bottom,
        'left': closest_left
    }