import cv2
import numpy as np


def check_overlap(rect1, rect2):
    """Check if two rectangles overlap"""
    x1, y1, w1, h1 = rect1
    x2, y2, w2, h2 = rect2
    return not (x1 + w1 < x2 or x2 + w2 < x1 or y1 + h1 < y2 or y2 + h2 < y1)


def calculate_distance(rect1, rect2):
    """Calculate minimum distance between two rectangles"""
    x1, y1, w1, h1 = rect1
    x2, y2, w2, h2 = rect2

    # Find centers
    c1x, c1y = x1 + w1/2, y1 + h1/2
    c2x, c2y = x2 + w2/2, y2 + h2/2

    # Find closest points
    dx = max(abs(c1x - c2x) - (w1 + w2)/2, 0)
    dy = max(abs(c1y - c2y) - (h1 + h2)/2, 0)

    return np.sqrt(dx*dx + dy*dy)


def calculate_distances_matrix(positions, bboxes):
    """Efficiently calculate distances between all positions and bboxes using numpy"""
    pos_centers = np.array([(x + w/2, y + h/2) for x, y, w, h in positions])
    bbox_centers = np.array([(x1 + (x2-x1)/2, y1 + (y2-y1)/2)
                            for x1, y1, x2, y2 in bboxes])

    # Broadcasting to calculate distances all at once
    return np.min(np.linalg.norm(pos_centers[:, np.newaxis] - bbox_centers, axis=2), axis=1)


def check_bbox_collision(label_rect, all_bboxes, parent_bbox):
    """Check if label rectangle collides with any bounding box except its parent"""
    x, y, w, h = label_rect
    label_rect = (x, y, x + w, y + h)  # Convert to x1,y1,x2,y2 format

    for bbox in all_bboxes:
        if bbox == parent_bbox:  # Skip parent box
            continue
        if (label_rect[0] < bbox[2] and label_rect[2] > bbox[0] and
                label_rect[1] < bbox[3] and label_rect[3] > bbox[1]):
            return True
    return False


def calculate_edge_spaces(bbox, all_bboxes, image_shape):
    """Calculate available space around each edge of the bounding box, considering neighbouring bboxes"""
    x1, y1, x2, y2 = bbox
    spaces = {
        'top': float('inf'),
        'bottom': float('inf'),
        'left': float('inf'),
        'right': float('inf')
    }

    for other_bbox in all_bboxes:
        if other_bbox == bbox:
            continue

        ox1, oy1, ox2, oy2 = other_bbox

        # Check top space
        if max(x1, ox1) < min(x2, ox2) and oy2 <= y1:
            spaces['top'] = min(spaces['top'], y1 - oy2)

        # Check bottom space
        if max(x1, ox1) < min(x2, ox2) and oy1 >= y2:
            spaces['bottom'] = min(spaces['bottom'], oy1 - y2)

        # Check left space
        if max(y1, oy1) < min(y2, oy2) and ox2 <= x1:
            spaces['left'] = min(spaces['left'], x1 - ox2)

        # Check right space
        if max(y1, oy1) < min(y2, oy2) and ox1 >= x2:
            spaces['right'] = min(spaces['right'], ox1 - x2)

    # Consider image boundaries
    spaces['top'] = min(spaces['top'], y1)
    spaces['bottom'] = min(spaces['bottom'], image_shape[0] - y2)
    spaces['left'] = min(spaces['left'], x1)
    spaces['right'] = min(spaces['right'], image_shape[1] - x2)

    return spaces


def get_candidate_positions(bbox, label_size, padding=5, edge_spaces=None):
    """Generate more diverse candidate positions with padding and edge space preference"""
    x1, y1, x2, y2 = bbox
    lw, lh = label_size
    width = x2 - x1
    height = y2 - y1

    positions = []

    if edge_spaces:
        # Sort edges by available space
        edges = sorted(edge_spaces.items(), key=lambda x: x[1], reverse=True)

        # Generate positions for each edge, starting with most spacious
        for edge, space in edges:
            if space < padding + 1:  # Need some minimal space
                continue

            if edge == 'top':
                positions.extend([
                    (x1 + int((width - lw) / 2), y1 - lh - padding, lw, lh),  # Top Center
                    (x1 + padding, y1 - lh - padding, lw, lh),                # Top Left
                    (x2 - lw - padding, y1 - lh - padding, lw, lh)            # Top Right
                ])
            elif edge == 'bottom':
                positions.extend([
                    (x1 + int((width - lw) / 2), y2 + padding, lw, lh),      # Bottom Center
                    (x1 + padding, y2 + padding, lw, lh),                    # Bottom Left
                    (x2 - lw - padding, y2 + padding, lw, lh)                # Bottom Right
                ])
            elif edge == 'left':
                positions.extend([
                    (x1 - lw - padding, y1 + int((height - lh) / 2), lw, lh),  # Left Center
                    (x1 - lw - padding, y1 + padding, lw, lh),                # Left Top
                    (x1 - lw - padding, y2 - lh - padding, lw, lh)            # Left Bottom
                ])
            elif edge == 'right':
                positions.extend([
                    (x2 + padding, y1 + int((height - lh) / 2), lw, lh),      # Right Center
                    (x2 + padding, y1 + padding, lw, lh),                    # Right Top
                    (x2 + padding, y2 - lh - padding, lw, lh)                # Right Bottom
                ])
    else: # Fallback positions - might not be needed if edge_spaces always provided
        positions.extend([
            (x1 + int((width - lw) / 2), y1 - lh - padding, lw, lh),  # Top Center
            (x1 + padding, y1 - lh - padding, lw, lh),                # Top Left
            (x2 - lw - padding, y1 - lh - padding, lw, lh),            # Top Right
            (x1 + int((width - lw) / 2), y2 + padding, lw, lh),      # Bottom Center
            (x1 + padding, y2 + padding, lw, lh),                    # Bottom Left
            (x2 - lw - padding, y2 + padding, lw, lh),                # Bottom Right
            (x1 - lw - padding, y1 + int((height - lh) / 2), lw, lh),  # Left Center
            (x1 - lw - padding, y1 + padding, lw, lh),                # Left Top
            (x1 - lw - padding, y2 - lh - padding, lw, lh),            # Left Bottom
            (x2 + padding, y1 + int((height - lh) / 2), lw, lh),      # Right Center
            (x2 + padding, y1 + padding, lw, lh),                    # Right Top
            (x2 + padding, y2 - lh - padding, lw, lh)                # Right Bottom
        ])
    return positions


def find_best_position(bbox, label_size, image_shape, existing_labels, all_bboxes, edge_spaces):
    """Find best non-colliding label position using scoring and considering edge spaces"""
    candidate_positions = get_candidate_positions(bbox, label_size, edge_spaces=edge_spaces)
    best_position = None
    max_score = -float('inf')

    for pos in candidate_positions:
        if not is_position_valid(pos, image_shape):
            continue

        if check_label_collision(pos, existing_labels):
            continue

        if check_bbox_collision(pos, all_bboxes, bbox): # Avoid label overlapping bbox
            continue

        score = calculate_position_score(pos, all_bboxes, existing_labels, bbox, image_shape, edge_spaces)

        if score > max_score:
            max_score = score
            best_position = pos

    if best_position:
        return best_position

    # If no non-colliding position found, try to reduce label size (optional and more complex)
    # For now, fallback to the first valid position (if any) or original position if no valid one at all.
    for pos in candidate_positions:
        if is_position_valid(pos, image_shape) and not check_label_collision(pos, existing_labels): # Relax bbox collision temporarily to find *any* valid position
            return pos

    return candidate_positions[0] if candidate_positions else (bbox[0], bbox[1]-label_size[1]-5, label_size[0], label_size[1]) # extreme fallback, place top-left if desperate


def is_position_valid(pos, image_shape, margin=2):
    """Check if label position is within image bounds with a margin"""
    x, y, w, h = pos
    return (x >= margin and y >= margin and x + w <= image_shape[1] - margin and y + h <= image_shape[0] - margin)


def check_label_collision(label_rect, existing_labels):
    """Check if label rectangle collides with any existing labels"""
    for existing_label in existing_labels:
        if check_overlap(label_rect, existing_label):
            return True
    return False


def calculate_position_score(pos, all_bboxes, all_labels, parent_bbox, image_shape, edge_spaces):
    """Calculate weighted score for position based on multiple factors"""
    x, y, w, h = pos
    MARGIN = 5  # Minimum distance from any box edge

    if not is_position_valid(pos, image_shape, MARGIN): # Check margin for image boundary
        return -float('inf')

    # Convert to x1,y1,x2,y2 format
    pos_rect = (x, y, x + w, y + h)

    # Check for collisions with margin around bboxes
    for bbox in all_bboxes:
        if bbox != parent_bbox:
            if (pos_rect[0] < bbox[2] + MARGIN and pos_rect[2] > bbox[0] - MARGIN and
                    pos_rect[1] < bbox[3] + MARGIN and pos_rect[3] > bbox[1] - MARGIN):
                return -float('inf')

    # Check label overlaps
    if check_label_collision(pos, all_labels):
        return -float('inf')


    # Calculate distance to other bboxes - prioritize positions far from other boxes
    distance_score = 0
    pos_center = (x + w / 2, y + h / 2)
    for bbox in all_bboxes:
        if bbox != parent_bbox:
            bbox_center = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
            dist = np.sqrt((pos_center[0] - bbox_center[0]) ** 2 + (pos_center[1] - bbox_center[1]) ** 2)
            distance_score += dist # Sum of distances - encourages positions far from *all* boxes


    # Edge preference score - favour edges with more space
    edge_score = 0
    parent_x1, parent_y1, parent_x2, parent_y2 = parent_bbox

    if abs(y - (parent_y1 - h)) < MARGIN:  # Top edge
        edge_score = edge_spaces['top']
    elif abs(y - parent_y2) < MARGIN:  # Bottom edge
        edge_score = edge_spaces['bottom']
    elif abs(x - (parent_x1 - w)) < MARGIN:  # Left edge
        edge_score = edge_spaces['left']
    elif abs(x - parent_x2) < MARGIN:  # Right edge
        edge_score = edge_spaces['right']


    # Combine scores with weights - adjust weights to fine-tune behaviour
    DISTANCE_WEIGHT = 0.5
    EDGE_WEIGHT = 0.5

    return (DISTANCE_WEIGHT * distance_score + EDGE_WEIGHT * edge_score)


def optimize_label_positions(components, scaled_bboxes, label_sizes, image_shape):
    """Optimize label positions to avoid overlaps and maximize distance, using edge space preference directly in position finding."""
    final_positions = []
    existing_label_rects = []

    edge_spaces_list = [calculate_edge_spaces(bbox, scaled_bboxes, image_shape)
                        for bbox in scaled_bboxes]

    for i, (bbox, label_size, edge_spaces) in enumerate(zip(scaled_bboxes, label_sizes, edge_spaces_list)):
        best_position = find_best_position(bbox, label_size, image_shape, existing_label_rects, scaled_bboxes, edge_spaces)
        final_positions.append(best_position)
        existing_label_rects.append(best_position) # Add current label as existing for next labels

    return final_positions


def draw_bounding_box(org, scaling_factor, components, color=(0, 0, 255), line=1,
                      show=False, write_path=None, name='board', is_return=False,
                      wait_key=0):
    """Drawing function with optimized label positioning"""
    if not show and write_path is None and not is_return:
        return

    board = org.copy()

    # 1. Pre-calculate bounding boxes and label sizes
    scaled_bboxes = []
    label_sizes = []
    font_scale = 0.5
    thickness = 1
    font_face = cv2.FONT_HERSHEY_DUPLEX

    for c in components:
        bbox = c.put_bbox()
        scaled_bbox = (
            int(bbox[0]/scaling_factor + 3),
            int(bbox[1]/scaling_factor - 0.8),
            int(bbox[2]/scaling_factor + 3),
            int(bbox[3]/scaling_factor - 0.8)
        )
        scaled_bboxes.append(scaled_bbox)

        label = str(c.id)
        label_size = cv2.getTextSize(
            label, font_face, font_scale, thickness)[0]
        label_sizes.append(label_size)

    # 2. Optimize label positions
    label_positions = optimize_label_positions(components, scaled_bboxes, label_sizes, board.shape[:2]) # Pass image height and width


    # 3. Draw boxes and labels
    padding = 2
    for compo, scaled_bbox, label_pos in zip(components, scaled_bboxes, label_positions):
        # Draw bounding box
        pt1 = (scaled_bbox[0], scaled_bbox[1])
        pt2 = (scaled_bbox[2], scaled_bbox[3])
        cv2.rectangle(board, pt1, pt2, color, line)

        # Draw label background - use label_pos which is (x, y, w, h) now
        bg_x = int(label_pos[0] - padding + 0.5)
        bg_y = int(label_pos[1] - padding + 0.5)
        bg_w = int(label_pos[2] + 2*padding + 0.5)
        bg_h = int(label_pos[3] + 2*padding + 0.5)

        cv2.rectangle(board,
                      (bg_x, bg_y),
                      (bg_x + bg_w, bg_y + bg_h),
                      (0, 0, 255), -1)

        # Draw label text
        label = str(compo.id)
        text_x = int(label_pos[0] + 0.5)
        text_y = int(label_pos[1] + label_pos[3] + 0.5) # use label_pos[3] (label height) for correct y

        cv2.putText(board, label,
                    (text_x, text_y),
                    font_face, font_scale, (255, 255, 255),
                    thickness, cv2.LINE_AA)

    if show:
        cv2.imshow(name, board)
        if wait_key is not None:
            cv2.waitKey(wait_key)
        if wait_key == 0:
            cv2.destroyWindow(name)

    if write_path is not None:
        cv2.imwrite(write_path, board)
    return board