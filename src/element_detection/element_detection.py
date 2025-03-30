from os.path import join as pjoin
import cv2
import os
import src.element_detection.detect_compo.ip_region_proposal as ip


def resize_height_by_longest_edge(img_path, resize_length=800):
    org = cv2.imread(img_path)
    height, width = org.shape[:2]
    if height > width:
        return resize_length
    else:
        return int(resize_length * (height / width))


def process_image(input_path_img, output_root, full_screen=False, min_grad=10, ffl_block=5, min_ele_area=50):
    key_params = {'min-grad': min_grad, 'ffl-block': ffl_block,
                  'min-ele-area': min_ele_area, 'merge-contained-ele': False}
    resized_height = resize_height_by_longest_edge(input_path_img)
    os.makedirs(pjoin(output_root), exist_ok=True)
    ip.compo_detection(input_path_img, output_root, full_screen, key_params,
                       resize_by_height=resized_height, show=False, wait_key=10)


if __name__ == '__main__':
    print('Running test')
    process_image(
        r'raw/screenshot.png', 'data/output')
