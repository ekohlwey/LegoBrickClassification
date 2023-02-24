# blender imports
import bpy
from mathutils import Euler, Vector

# python imports
import argparse
import sys
import os
import logging
import random
import math


sys.path.append('dataset')


def render_settings(render_folder):
    os.makedirs(render_folder, exist_ok=True)
    bpy.context.scene.render.engine = 'CYCLES'
    render = bpy.data.scenes['Scene'].render
    render.resolution_x = 100
    render.resolution_y = 100
    render.resolution_percentage = 100
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.render.image_settings.color_mode = "RGB"
    bpy.context.scene.render.image_settings.quality = 70
    return render


def check_blender():
    if not bpy.context.space_data:
        cwd = os.path.dirname(os.path.abspath(__file__))
    else:
        cwd = os.path.dirname(bpy.context.space_data.text.filepath)
    # get folder of script and add current working directory to path
    sys.path.append(cwd)


def deselect_all():
    bpy.ops.object.select_all(action='DESELECT')


def render_brick(brick_file_path, number_of_images, render_folder):
    render = render_settings(render_folder)
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


def remove_initital_cube():
    bpy.data.objects["Cube"].select_set(True)
    bpy.ops.object.delete()


def add_ground_plane():
    deselect_all()
    bpy.ops.mesh.primitive_plane_add()
    new_plane = bpy.context.selected_objects[0]
    new_plane.name = "Ground"
    new_plane.scale = (10000, 10000, 1)
    bpy.ops.rigidbody.object_add(type='PASSIVE')


def find_brick_object():
    collection = next(x for x in bpy.data.collections if x.name.endswith(".dat"))
    return collection.children['Parts'].objects[0]


def random_angle():
    return random.uniform(0, 2 * math.pi)


def select_object(obj):
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def setup_brick_simulation():
    deselect_all()
    brick = find_brick_object()
    bpy.ops.rigidbody.object_add(type='ACTIVE')
    brick.location = (0, 0, brick.dimensions.z * 2)
    brick.rigid_body.collision_shape = 'MESH'
    brick.rotation_euler = (random_angle(), random_angle(), random_angle())
    select_object(brick)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)


def simulate():
    pc = bpy.context.scene.rigidbody_world.point_cache
    bpy.ops.ptcache.bake({"point_cache": pc}, bake=True)
    bpy.context.scene.frame_set(250)


def setup_rigid_body_world():
    bpy.ops.rigidbody.world_add()


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

    remove_initital_cube()
    setup_rigid_body_world()
    add_ground_plane()
    render_brick(args.input, args.number, args.save)
