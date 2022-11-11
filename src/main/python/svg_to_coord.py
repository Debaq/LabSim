from xml.dom import minidom
from svg.path import parse_path
from base import context

file = context.get_resource('test_abr.svg')
doc = minidom.parse(file)



for ipath, path in enumerate(doc.getElementsByTagName('path')):
    print('Path', ipath)
    d = path.getAttribute('d')
    parsed = parse_path(d)
    print('Objects:\n', parsed, '\n' + '-' * 20)
    for obj in parsed:
        print(type(obj).__name__, ', start/end coords:', ((round(obj.start.real, 3), round(obj.start.imag, 3)), (round(obj.end.real, 3), round(obj.end.imag, 3))))
    print('-' * 20)
doc.unlink()



from svg_to_gcode.svg_parser import parse_file
from svg_to_gcode.compiler import Compiler, interfaces

# Instantiate a compiler, specifying the interface type and the speed at which the tool should move. pass_depth controls
# how far down the tool moves after every pass. Set it to 0 if your machine does not support Z axis movement.
gcode_compiler = Compiler(interfaces.Gcode, movement_speed=1000, cutting_speed=300, pass_depth=5)

curves = parse_file(file) # Parse an svg file into geometric curves

gcode_compiler.append_curves(curves) 
gcode_compiler.compile_to_file("drawing.gcode", passes=1)