import bpy
import os
import sys
import logging
import datetime


def warning_text():
    camera = bpy.context.scene.camera
    empt = bpy.data.objects.new("empty", None)

    font_curve = bpy.data.curves.new(type="FONT", name="take_warning")
    font_curve.body = "TAKE!"
    font_curve.align_x = "CENTER"
    font_curve.align_y = "CENTER"
    obj = bpy.data.objects.new(name="Font Object", object_data=font_curve)

    # Material
    mat_name = "take_warning"
    warning_mat = bpy.data.materials.get(mat_name)
    if not warning_mat:
        warning_mat = bpy.data.materials.new(mat_name)
        warning_mat.diffuse_color[0] = 1
        warning_mat.diffuse_color[1] = 0
        warning_mat.diffuse_color[2] = 0

    obj.data.materials.append(warning_mat)
    obj.parent = empt
    obj.hide_render = True
    obj.show_in_front = True

    # Copy transform constraint
    con = empt.constraints.new(type="COPY_TRANSFORMS")
    con.target = camera
    scale_fac = 0.35
    obj.location.z = camera.data.lens * -0.028
    obj.scale.xyz = (scale_fac, scale_fac, scale_fac)

    # Collection
    collection_name = "take_warning"
    parent_collection = bpy.context.scene.collection
    layer_collection = bpy.context.view_layer.layer_collection

    if not collection_name in bpy.data.collections:
        new_collection = bpy.data.collections.new(collection_name)
        layer_collection.collection.children.link(new_collection)

    bpy.data.collections[collection_name].objects.link(obj)
    bpy.data.collections[collection_name].objects.link(empt)


logger = logging.getLogger(__name__)
FORMAT = "%(message)s"
logging.basicConfig(filename="takes.log", level=logging.INFO, format=FORMAT)
logger.info("------\n{} Takes Processing".format(datetime.datetime.now()))

argv = sys.argv
takenames = argv[argv.index("--") + 1 :]  # get all args after "--"


# Get blendfile path and name
main_file = bpy.data.filepath
path_and_file = os.path.split(main_file)
blendpath = os.path.join(path_and_file[0])
filename = os.path.splitext(path_and_file[1])[0]  # w/o extension

output_path = os.path.join(
    blendpath,
    "output",
    filename,
)

os.makedirs(output_path, exist_ok=True)

# if takenames empty, process all
if not len(takenames):

    def vdir(obj):
        return [x for x in dir(obj) if x.startswith(("take_"))]

    takes = bpy.data.texts["takes"].as_module()
    takenames = vdir(takes)

for name in takenames:
    print("\n\n------ Processing Take", name, " ------")
    output_file = os.path.join(output_path, filename + "." + name + ".blend")

    # Find script data-block named "takes"
    takes = bpy.data.texts["takes"].as_module()
    take_def = getattr(takes, name)
    take_def()

    take_data_block = bpy.data.texts["takes"]
    take_data_block.clear()
    take_data_block.write("this is a renderfile")

    # Setup warning text. This is so there is some indication
    # to not accidentally do work in this file.
    warning_text()

    # Renderoutput path
    render_out_path = "//render/{a}/{b}.".format(a=name, b=name)
    bpy.context.scene.render.filepath = render_out_path
    print("Render output path", render_out_path)

    # Save
    bpy.ops.wm.save_as_mainfile(copy=True, check_existing=False, filepath=output_file)

    # Write to log file. This is for the Simple Render Queue:
    frame_range = [str(bpy.context.scene.frame_start), str(bpy.context.scene.frame_end)]
    logger.info("{} -c 1 -f {}".format(output_file, "-".join(frame_range)))

    # Re-open original file
    bpy.ops.wm.open_mainfile(filepath=main_file)
