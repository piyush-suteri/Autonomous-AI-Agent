from os.path import join as pjoin
import time
import cv2

import src.element_detection.detect_compo.lib_ip.ip_preprocessing as pre
import src.element_detection.detect_compo.lib_ip.ip_draw as draw
import src.element_detection.detect_compo.lib_ip.ip_detection as det
import src.element_detection.detect_compo.lib_ip.file_utils as file
import src.element_detection.detect_compo.lib_ip.Component as Compo
from src.element_detection.config.CONFIG_UIED import Config
from src.backend.utils import core_utils
C = Config()


def nesting_inspection(org, grey, compos, ffl_block):
    '''
    Inspect all big compos through block division by flood-fill
    :param ffl_block: gradient threshold for flood-fill
    :return: nesting compos
    '''
    nesting_compos = []
    for i, compo in enumerate(compos):
        if compo.height > 50:
            replace = False
            clip_grey = compo.compo_clipping(grey)
            n_compos = det.nested_components_detection(
                clip_grey, org, grad_thresh=ffl_block, show=False)
            Compo.cvt_compos_relative_pos(
                n_compos, compo.bbox.col_min, compo.bbox.row_min)

            for n_compo in n_compos:
                if n_compo.redundant:
                    compos[i] = n_compo
                    replace = True
                    break
            if not replace:
                nesting_compos += n_compos
    return nesting_compos


def compo_detection(input_img_path, output_root, full_screen, uied_params,
                    resize_by_height=800, show=False, wait_key=0):

    start = time.perf_counter()
    name = input_img_path.split(
        '/')[-1][:-4] if '/' in input_img_path else input_img_path.split('\\')[-1][:-4]

    # *** Step 1 *** pre-processing: read img -> get binary map
    org, grey = pre.read_img(input_img_path, resize_by_height)
    binary = pre.binarization(org, grad_min=int(uied_params['min-grad']))

    # *** Step 2 *** element detection
    det.rm_line(binary, show=show, wait_key=wait_key)
    uicompos = det.component_detection(
        binary, min_obj_area=int(uied_params['min-ele-area']))

    # *** Step 3 *** results refinement
    uicompos = det.compo_filter(uicompos, min_area=int(
        uied_params['min-ele-area']), img_shape=binary.shape)
    uicompos = det.merge_intersected_compos(uicompos)
    det.compo_block_recognition(binary, uicompos)
    if uied_params['merge-contained-ele']:
        uicompos = det.rm_contained_compos_not_in_block(uicompos)
    Compo.compos_update(uicompos, org.shape)
    Compo.compos_containment(uicompos)

    # *** Step 4 ** nesting inspection: check if big compos have nesting element
    original_image = cv2.imread(input_img_path)
    origianl_height = cv2.imread(input_img_path).shape[0]
    scaling_factor = resize_by_height / origianl_height

    uicompos += nesting_inspection(org, grey,
                                   uicompos, ffl_block=uied_params['ffl-block'])
    Compo.compos_update(uicompos, org.shape)
    draw.draw_bounding_box(original_image, scaling_factor, uicompos, show=show, name='merged compo', write_path=pjoin(
        output_root, name + '.png'), wait_key=wait_key)

    # *** Step 7 *** save detection result
    Compo.compos_update(uicompos, org.shape)
    file.save_corners_json(pjoin(output_root, name + '.json'), uicompos, full_screen)

    core_utils.log("[element_detection]: [Compo Detection Completed in %.3f s] Input: %s Output: %s" % (
        time.perf_counter() - start, input_img_path, pjoin(output_root, name + '.json')))
