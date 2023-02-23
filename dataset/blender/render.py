# blender imports
import bpy
from mathutils import Euler, Vector

# python imports
import argparse
import sys
import re
import os
import logging
import random
from copy import deepcopy

import numpy as np

print('numpy version: {}'.format(np.__version__))
sys.path.append('dataset')
from blender import sphere
from blender.utils import hex2rgb, deg2rad, random_like_color
import json


def _render_settings(render_folder, render_cfg):
    os.makedirs(render_folder, exist_ok=True)
    bpy.context.scene.render.engine = 'CYCLES'
    render = bpy.data.scenes['Scene'].render
    render.resolution_x = render_cfg['width']
    render.resolution_y = render_cfg['height']
    render.resolution_percentage = render_cfg['resolution']
    bpy.context.scene.render.image_settings.file_format = render_cfg['format']
    bpy.context.scene.render.image_settings.color_mode = render_cfg['color_mode']
    bpy.context.scene.render.image_settings.quality = render_cfg['quality']  # compression in range [0, 100]
    return render


def check_blender():
    if bpy.context.space_data == None:
        cwd = os.path.dirname(os.path.abspath(__file__))
    else:
        cwd = os.path.dirname(bpy.context.space_data.text.filepath)
    # get folder of script and add current working directory to path
    sys.path.append(cwd)


def render_brick(brick_file_path, number_of_images, render_folder, cfg):
    render = _render_settings(render_folder, cfg['render'])
    bpy.ops.ldraw_exporter.import_operator(filepath=brick_file_path)
    for i in range(number_of_images):
        # render image
        brick_class = os.path.splitext(os.path.basename(brick_file_path))[0]
        render.filepath = os.path.join(render_folder, brick_class + '_' + str(i) + '.jpg')
        bpy.ops.render.render(write_still=True)
    return


def parse_args(parser):
    parser.add_argument(
        "-i", "--input_file_path", dest="input", type=str, required=True,
        help="Input 3d model"
    )

    parser.add_argument(
        "-n", "--images_per_brick", dest="number", type=int, required=False, default=1,
        help="number of images to render"
    )

    parser.add_argument(
        "-s", "--save", dest="save", type=str, required=False, default="./",
        help="output folder"
    )

    parser.add_argument(
        "-c", "--config", dest="config", required=False, default='augmentation.json',
        help="path to config file"
    )

    parser.add_argument(
        "-v", "--verbose", required=False, action="store_true",
        help="verbosity mode and log to file"
    )

    return parser.parse_args(argv)


if __name__ == '__main__':

    # check if script is opened in blender program
    check_blender()
    argv = sys.argv

    if "--" not in argv:
        argv = []
    else:
        argv = argv[argv.index("--") + 1:]  # get all after first --

    # when --help or no args are given
    usage_text = (
            "Run blender in background mode with this script:"
            " blender -b -P " + __file__ + "-- [options]"
    )
    parser = argparse.ArgumentParser(description=usage_text)
    args = parse_args(parser)

    if not argv:
        parser.print_help()
        sys.exit(-1)
    if not (args.input or args.background):
        print("Error: Some required arguments missing")
        parser.print_help()
        sys.exit(-1)

    # load config file for blender settings
    cfg_path = os.path.join(os.path.dirname(__file__), 'configs', args.config)
    with open(cfg_path, 'r') as fr:
        cfg = json.load(fr)

    # init logger
    brick_id = os.path.splitext(os.path.basename(args.input))[0]
    format = '%(asctime)s [%(levelname)s] %(message)s'
    level = logging.INFO
    if args.verbose:
        level = logging.DEBUG
        log_filename = os.path.join(args.save, 'logs', brick_id + '.log')
        os.makedirs(os.path.dirname(log_filename), exist_ok=True)
        logging.basicConfig(filename=log_filename, level=level, filemode='w', format=format)
    else:
        logging.basicConfig(level=level, filemode='w', format=format)
    logging.info('config file: %s', args.config)
    logging.getLogger().addHandler(logging.StreamHandler())

    bpy.data.objects["Cube"].select_set(True)
    bpy.ops.object.delete()
    # try:
    render_brick(args.input, args.number, args.save, cfg)
    # except Exception as e:
    #    logging.error(e)
