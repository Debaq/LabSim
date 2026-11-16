"""La pieza del laboratorio de sueño, con el paciente acostado, renderizada con Blender.

Uso:
  blender -b -P scripts/psg_pieza/gen_pieza.py -- todo <carpeta> [pose ...]
  blender -b -P scripts/psg_pieza/gen_pieza.py -- muestra <carpeta> [supino|izquierda|derecha] [despierto]
  (PSG_CARA=1 agrega un primer plano de la cara a la muestra)

<entrada> (fija): ~/.cache/labsim/psg_mh, lo que exporta MakeHuman con makehuman.json (ver LEEME.md).
El cuerpo, el pelo y las expresiones vienen de MakeHuman; la cama, la pieza, la frazada (tela
simulada sobre el cuerpo) y los sensores de la polisomnografía se arman acá. Se renderiza lo que
se ve por la ventanilla de la sala de control y lo que ve la cámara del techo.

Importar y normalizar el FBX de MakeHuman y pasar las expresiones a shape keys viene de
Misión Reponedor (tools/gen_personaje_mh.py).
"""
import json
import math
import os
import pathlib
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
from bpy_extras.object_utils import world_to_camera_view

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
MH = pathlib.Path(os.path.expanduser('~/.cache/labsim/psg_mh'))

# ── colores y materiales ────────────────────────────────────────────────────


def lineal(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexa(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


_mats = {}


def mat(color, rough=0.7, nombre=None, emision=0.0):
    clave = (color, rough, nombre, emision)
    if clave in _mats:
        return _mats[clave]
    m = bpy.data.materials.new(name=nombre or f'm{len(_mats)}')
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    rgb = (*[lineal(c) for c in hexa(color)], 1)
    b.inputs['Base Color'].default_value = rgb
    b.inputs['Roughness'].default_value = rough
    if 'Specular IOR Level' in b.inputs:
        b.inputs['Specular IOR Level'].default_value = 0.3
    if emision:
        b.inputs['Emission Color'].default_value = rgb
        b.inputs['Emission Strength'].default_value = emision
    _mats[clave] = m
    return m


def poner(o, m):
    o.data.materials.clear()
    o.data.materials.append(m)
    return o


def biselar(o, ancho, segmentos=2):
    b = o.modifiers.new('bisel', 'BEVEL')
    b.width = ancho
    b.segments = segmentos
    b.limit_method = 'ANGLE'
    return o


def caja(cx, cy, cz, sx, sy, sz, color, rough=0.7, bisel=0.0, nombre=None):
    """Caja con centro (cx, cy, cz) y medidas (sx, sy, sz)."""
    bpy.ops.mesh.primitive_cube_add(location=(cx, cy, cz))
    o = bpy.context.object
    o.scale = (sx / 2, sy / 2, sz / 2)
    bpy.ops.object.transform_apply(scale=True)
    if nombre:
        o.name = nombre
    poner(o, mat(color, rough))
    if bisel:
        biselar(o, bisel, 3)
        bpy.ops.object.shade_smooth()
    return o


def cil(cx, cy, cz, r, h, color, eje='Z', n=24, rough=0.6):
    rot = {'Z': (0, 0, 0), 'X': (0, math.pi / 2, 0), 'Y': (math.pi / 2, 0, 0)}[eje]
    bpy.ops.mesh.primitive_cylinder_add(vertices=n, radius=r, depth=h, location=(cx, cy, cz), rotation=rot)
    o = bpy.context.object
    bpy.ops.object.shade_smooth()
    return poner(o, mat(color, rough))


# ── importar de MakeHuman (de Misión Reponedor) ─────────────────────────────


def activar(o):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = o
    o.select_set(True)


def importar(f):
    antes = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(f), global_scale=10.0)
    objs = [o for o in bpy.data.objects if o not in antes]
    normalizar(objs)
    return objs


def normalizar(objs):
    """El FBX de MakeHuman llega con el esqueleto girado y una pose base que lo pone de pie: esa pose
    pasa a ser el reposo (z arriba, mirando a -y, esqueleto sin giro, pose identidad)."""
    arm = next(o for o in objs if o.type == 'ARMATURE')
    mallas = [o for o in objs if o.type == 'MESH']
    bpy.context.view_layer.update()
    for o in mallas:
        activar(o)
        for m in list(o.modifiers):
            if m.type == 'ARMATURE':
                bpy.ops.object.modifier_apply(modifier=m.name)
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    activar(arm)
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.armature_apply(selected=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for o in mallas:
        o.parent = arm
        o.matrix_parent_inverse = Matrix.Identity(4)
        a = o.modifiers.new('esqueleto', 'ARMATURE')
        a.object = arm


def suavizar(o, subdividir=False):
    activar(o)
    if o.data.has_custom_normals:
        bpy.ops.mesh.customdata_custom_splitnormals_clear()
    bpy.ops.object.shade_smooth()
    if subdividir:
        m = o.modifiers.new('sub', 'SUBSURF')
        m.levels = 1
        m.render_levels = 2


def pegar(o, arm):
    mw = o.matrix_world.copy()
    o.parent = arm
    o.matrix_world = mw
    for m in o.modifiers:
        if m.type == 'ARMATURE':
            m.object = arm


def a_hueso(o, arm, hueso):
    bpy.context.view_layer.update()
    mw = o.matrix_world.copy()
    o.parent = arm
    o.parent_type = 'BONE'
    o.parent_bone = hueso
    bpy.context.view_layer.update()
    o.matrix_world = mw


def leer_obj(f):
    grupos, verts = [], []
    for linea in open(f):
        if linea.startswith('v '):
            verts.append(Vector(tuple(float(x) for x in linea.split()[1:4])))
        elif linea.startswith('g '):
            grupos.append(linea.split()[1].rsplit('.', 1)[0])
    return grupos, verts


EXPRESIONES = {'dormido': 'sleep01', 'boca': 'vocalize01'}


def expresiones(p):
    """Cada expresión de MakeHuman (OBJ con la misma topología) pasa a shape key de cada malla."""
    grupos, neutra = leer_obj(MH / 'paciente_expr_neutra.obj')
    destinos = []
    for g in grupos:
        o = p.cuerpo if g == 'base' else next((m for m in p.mallas if m.name.startswith(g)), None)
        assert o is not None, g
        destinos.append(o)
    desde, rangos = 0, []
    for o in destinos:
        rangos.append((o, desde))
        desde += len(o.data.vertices)
    assert desde == len(neutra), (desde, len(neutra))
    a_blender = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))
    zs = [(p.cuerpo.matrix_world @ v.co).z for v in p.cuerpo.data.vertices]
    ys = [v.y for v in neutra[:len(p.cuerpo.data.vertices)]]
    escala = (max(zs) - min(zs)) / (max(ys) - min(ys))
    for o, _ in rangos:
        if not o.data.shape_keys:
            o.shape_key_add(name='Basis', from_mix=False)
    for nombre, mh in EXPRESIONES.items():
        _, verts = leer_obj(MH / f'paciente_expr_{mh}.obj')
        for o, ini in rangos:
            inv = o.matrix_world.to_3x3().inverted()
            k = o.shape_key_add(name=nombre, from_mix=False)
            base = o.data.shape_keys.key_blocks['Basis'].data
            for i in range(len(o.data.vertices)):
                d = a_blender @ (verts[ini + i] - neutra[ini + i]) * escala
                k.data[i].co = base[i].co + inv @ d


# ── el paciente ─────────────────────────────────────────────────────────────


class Paciente:
    def __init__(self):
        objs = importar(MH / 'paciente_cuerpo.fbx')
        self.arm = next(o for o in objs if o.type == 'ARMATURE')
        self.mallas = [o for o in objs if o.type == 'MESH']
        self.cuerpo = next(o for o in self.mallas if o.name.startswith('paciente_cuerpo'))
        self.ropa = next(o for o in self.mallas if o.name.startswith('male_casualsuit'))
        for o in self.mallas:
            suavizar(o, subdividir=o in (self.cuerpo, self.ropa))
        for o in importar(MH / 'paciente_pelo_short02.fbx'):
            if o.type == 'MESH' and o.name.startswith('short02'):
                pegar(o, self.arm)
                suavizar(o)
                self.pelo = o
            else:
                bpy.data.objects.remove(o, do_unlink=True)
        expresiones(self)
        self.materiales()
        self.base = {pb.name: pb.matrix_basis.copy() for pb in self.arm.pose.bones}
        # Lo que apoya en la cama (sin manos ni pies). MakeHuman borra el cuerpo bajo la ropa: va la polera.
        self.tronco = []
        for o in (self.cuerpo, self.ropa):
            grupos = {g.index for g in o.vertex_groups
                      if g.name.startswith(('spine', 'pelvis', 'clavicle', 'shoulder', 'breast', 'upperleg', 'neck'))}
            self.tronco += [(o, v.index) for v in o.data.vertices
                            if sum(g.weight for g in v.groups if g.group in grupos) > 0.6]
        bpy.context.view_layer.update()
        self.alto = max((self.cuerpo.matrix_world @ v.co).z for v in self.cuerpo.data.vertices)

    def materiales(self):
        for o in [*self.mallas, self.pelo]:
            for m in o.data.materials:
                if not m or not m.use_nodes:
                    continue
                b = m.node_tree.nodes.get('Principled BSDF')
                if not b:
                    continue
                for n in m.node_tree.nodes:
                    if n.type == 'TEX_IMAGE':
                        n.interpolation = 'Cubic'   # el FBX la trae en 'Closest' (se ve pixelado)
                if o in (self.cuerpo, self.ropa) or o.name.startswith(('high-poly', 'teeth')):
                    # El FBX conecta el alfa de la textura: la piel y la ropa quedan transparentes.
                    for l in list(m.node_tree.links):
                        if l.to_socket == b.inputs['Alpha']:
                            m.node_tree.links.remove(l)
                    b.inputs['Alpha'].default_value = 1.0
                if o is self.cuerpo:
                    b.inputs['Roughness'].default_value = 0.55
                    if 'Subsurface Weight' in b.inputs:
                        b.inputs['Subsurface Weight'].default_value = 0.15
                        b.inputs['Subsurface Radius'].default_value = (0.01, 0.004, 0.002)
                elif o is self.ropa:
                    # Polera lisa (la de MakeHuman trae su logo): se queda con la textura en gris para
                    # las arrugas, teñida de celeste de pijama.
                    b.inputs['Roughness'].default_value = 0.9
                    nt = m.node_tree
                    for l in list(nt.links):
                        if l.to_socket == b.inputs['Base Color']:
                            nt.links.remove(l)
                    b.inputs['Base Color'].default_value = (*[lineal(c) for c in hexa('#9fb4c9')], 1)
                else:
                    b.inputs['Roughness'].default_value = 0.6

    def expresion(self, nombre, boca=0.0):
        """nombre: 'dormido' o None (despierto, ojos abiertos); boca: cuánto abre la boca (ronquido)."""
        for o in self.mallas:
            if o.data.shape_keys:
                for kb in o.data.shape_keys.key_blocks[1:]:
                    if kb.name == 'boca':
                        kb.value = boca
                    elif kb.name in EXPRESIONES:
                        kb.value = 1.0 if kb.name == nombre else 0.0

    def respirar(self, torax, abdomen):
        for o in self.respiran:
            kb = o.data.shape_keys.key_blocks
            kb['torax'].value = torax
            kb['abdomen'].value = abdomen

    def hueso(self, nombre, extremo='head'):
        pb = self.arm.pose.bones[nombre]
        return self.arm.matrix_world @ getattr(pb, extremo)

    def rotar(self, hueso, eje, grados):
        """Gira un hueso alrededor de su cabeza, con un eje del mundo (con el cuerpo de pie)."""
        pb = self.arm.pose.bones[hueso]
        cabeza = pb.head.copy()
        r = Matrix.Translation(cabeza) @ Matrix.Rotation(math.radians(grados), 4, Vector(eje)) @ \
            Matrix.Translation(-cabeza)
        pb.matrix = r @ pb.matrix
        bpy.context.view_layer.update()

    def posar(self, pose, despierto=False):
        """Pone la pose (de pie, sin girar) y acuesta el cuerpo sobre la cama. Despierto: la cabeza
        un poco girada (los ojos abiertos los pone la expresión)."""
        self.arm.matrix_world = Matrix.Identity(4)
        for pb in self.arm.pose.bones:
            pb.matrix_basis = self.base[pb.name]
        bpy.context.view_layer.update()
        for hueso, eje, grados in POSES[pose] + (DESPIERTO if despierto else []):
            lados = (('L', 1), ('R', -1)) if hueso.endswith('.X') else ((None, 1),)
            for lado, s in lados:
                nombre = hueso[:-2] + '.' + lado if lado else hueso
                self.rotar(nombre, (eje[0], eje[1] * s, eje[2] * s) if lado else eje, grados)
        # De pie mirando a -y -> de espaldas con la cabeza hacia +y; de lado: rueda sobre ese costado
        # (su izquierda es +x).
        giro = Matrix.Rotation(math.radians(-90), 4, 'X')
        rueda = {'supino': 0, 'izquierda': 100, 'derecha': -100}[pose]   # de lado, un poco hacia adelante
        giro = Matrix.Rotation(math.radians(rueda), 4, 'Y') @ giro
        self.arm.matrix_world = giro
        bpy.context.view_layer.update()
        # Apoyado en el colchón (por el tronco: las manos no cuentan), con la cabeza en la almohada.
        subs = [o.modifiers['sub'] for o in (self.cuerpo, self.ropa)]
        for m in subs:
            m.show_viewport = False
        dg = bpy.context.evaluated_depsgraph_get()
        ev = {o: o.evaluated_get(dg) for o in (self.cuerpo, self.ropa)}
        pts = [ev[o].matrix_world @ ev[o].data.vertices[i].co for o, i in self.tronco]
        for m in subs:
            m.show_viewport = True
        zs = [v.z for v in pts]
        xs = [v.x for v in pts]
        cab = self.hueso('head')
        dx = CAMA['x'] - (min(xs) + max(xs)) / 2 if pose == 'supino' else CAMA['x'] - cab.x
        dz = CAMA['colchon'] - 0.015 - min(zs)
        dy = CAMA['cabeza_y'] - cab.y
        self.arm.matrix_world = Matrix.Translation((dx, dy, dz)) @ giro
        bpy.context.view_layer.update()


DESPIERTO = [('neck02', (0, 0, 1), 16)]
# Poses: (hueso, eje del mundo con el cuerpo de pie mirando a -y, grados), de padres a hijos.
# '.X' = los dos lados (espejado). Flexión de cadera = muslo hacia -y (grados negativos en x).
# En el reposo de MakeHuman el antebrazo ya va ~47° hacia adelante: +40 lo deja casi estirado.
BRAZOS = [('upperarm01.X', (0, 1, 0), 30), ('lowerarm01.X', (1, 0, 0), 40)]
# De lado sobre el costado izquierdo (el derecho se espeja). Su izquierda (+x de pie) queda abajo, así
# que lo de arriba cae hacia +x: la rodilla y la mano de arriba se apoyan delante, en la cama.
LADO = [('spine02', (1, 0, 0), 10), ('neck01', (1, 0, 0), 12),
        ('upperarm01.L', (0, 1, 0), 24), ('upperarm01.L', (1, 0, 0), -70), ('lowerarm01.L', (1, 0, 0), -45),
        ('upperarm01.R', (0, -1, 0), 30), ('upperarm01.R', (1, 0, 0), -35), ('upperarm01.R', (0, 1, 0), -35),
        ('lowerarm01.R', (1, 0, 0), 10),
        ('upperleg01.L', (1, 0, 0), -30), ('lowerleg01.L', (1, 0, 0), 40),
        ('upperleg01.R', (1, 0, 0), -55), ('upperleg01.R', (0, 1, 0), -22), ('lowerleg01.R', (1, 0, 0), 75),
        ('foot.L', (1, 0, 0), 25), ('foot.R', (1, 0, 0), 25)]
POSES = {
    'supino': BRAZOS + [('neck01', (1, 0, 0), 10), ('foot.X', (1, 0, 0), 30)],
    'izquierda': LADO,
    'derecha': [(h[:-1] + {'L': 'R', 'R': 'L'}[h[-1]] if h.endswith(('.L', '.R')) else h,
                 (e[0], -e[1], -e[2]) if h.endswith(('.L', '.R')) else e, g) for h, e, g in LADO],
}

# ── la pieza ────────────────────────────────────────────────────────────────

CAMA = dict(x=0.0, ancho=1.0, largo=2.0, colchon=0.58, cabeza_y=0.80)
PARED_FONDO = 1.25      # pared de la cabecera (y)
PARED_PIES = -2.05      # pared de los pies (con la puerta)
PIEZA_X = (-1.7, 1.15)  # en x1 está la pared de la sala de control, con la ventanilla
ALTO_PIEZA = 2.6


def pieza():
    # Piso, paredes y cielo.
    x0, x1 = PIEZA_X
    caja((x0 + x1) / 2, (PARED_FONDO + PARED_PIES) / 2, -0.01, x1 - x0, PARED_FONDO - PARED_PIES, 0.02,
         '#9b958a', 0.5, nombre='piso')
    caja((x0 + x1) / 2, PARED_FONDO + 0.05, ALTO_PIEZA / 2, x1 - x0, 0.1, ALTO_PIEZA, '#c9cdc4', 0.9)
    caja(x0 - 0.05, (PARED_FONDO + PARED_PIES) / 2, ALTO_PIEZA / 2, 0.1, PARED_FONDO - PARED_PIES,
         ALTO_PIEZA, '#c4c8bf', 0.9)
    # Pared de los pies, con la puerta.
    caja((x0 + x1) / 2, PARED_PIES - 0.05, ALTO_PIEZA / 2, x1 - x0, 0.1, ALTO_PIEZA, '#c4c8bf', 0.9)
    caja(-0.9, PARED_PIES + 0.005, 1.0, 0.9, 0.03, 2.0, '#8a7360', 0.6, bisel=0.005)
    cil(-0.55, PARED_PIES + 0.04, 1.0, 0.012, 0.06, '#c0c0c0', eje='Y', rough=0.3)
    caja((x0 + x1) / 2, (PARED_FONDO + PARED_PIES) / 2, ALTO_PIEZA + 0.05, x1 - x0, PARED_FONDO - PARED_PIES,
         0.1, '#d8d8d2', 0.9)
    # Zócalo.
    caja((x0 + x1) / 2, PARED_FONDO - 0.005, 0.05, x1 - x0, 0.02, 0.1, '#7d776d', 0.6)
    # Cama: base de madera, colchón, sábana de abajo y almohada.
    c = CAMA
    caja(c['x'], 0, 0.2, c['ancho'] + 0.08, c['largo'] + 0.06, 0.24, '#6b5544', 0.6, bisel=0.01)
    for px in (-1, 1):
        for py in (-1, 1):
            caja(c['x'] + px * (c['ancho'] / 2 - 0.02), py * (c['largo'] / 2 - 0.02), 0.05, 0.06, 0.06, 0.1,
                 '#4e3d30', 0.6)
    caja(c['x'], PARED_FONDO - 0.04, 0.7, c['ancho'] + 0.12, 0.05, 0.9, '#6b5544', 0.6, bisel=0.015,
         nombre='respaldo')
    colchon = caja(c['x'], 0, (0.32 + c['colchon']) / 2, c['ancho'], c['largo'], c['colchon'] - 0.32,
                   '#e9ebe6', 0.85, bisel=0.06, nombre='colchon')
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(c['x'], c['cabeza_y'] + 0.04, c['colchon'] + 0.05))
    alm = bpy.context.object
    alm.name = 'almohada'
    alm.scale = (0.33, 0.2, 0.065)
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.shade_smooth()
    poner(alm, mat('#f1f2ef', 0.85))
    # Velador con el cabezal de la polisomnografía, a la derecha del paciente (-x).
    vx = c['x'] - c['ancho'] / 2 - 0.35
    caja(vx, 0.95, 0.3, 0.45, 0.4, 0.6, '#7a6150', 0.6, bisel=0.01)
    caja(vx, 0.95, 0.66, 0.26, 0.18, 0.12, '#2f3337', 0.4, bisel=0.008, nombre='cabezal')
    caja(vx + 0.07, 0.86, 0.68, 0.03, 0.005, 0.015, '#66ff88', 0.3)
    # Lámpara de noche (luz baja y cálida) en el velador.
    cil(vx - 0.12, 1.02, 0.63, 0.05, 0.06, '#d9d4c7')
    cil(vx - 0.12, 1.02, 0.78, 0.07, 0.12, '#f3e6c8', rough=0.9)
    # Cámara infrarroja en la esquina del cielo.
    cil(x1 - 0.15, PARED_FONDO - 0.15, ALTO_PIEZA - 0.06, 0.06, 0.08, '#2c2c2c')
    # Cortina en la pared del frente (la que se ve por la ventanilla).
    caja(x0 + 0.06, -0.6, 1.4, 0.04, 1.4, 2.2, '#5d6d7e', 0.95)
    # Cuadro en la pared.
    caja(x0 + 0.03, 0.55, 1.55, 0.03, 0.6, 0.42, '#a89f8a', 0.6)
    return colchon, alm


def ventanilla():
    """La pared de la sala de control (al lado izquierdo del paciente), con la ventanilla. Sin vidrio:
    el reflejo lo pone LabSim encima."""
    y0, y1 = PARED_PIES, PARED_FONDO
    x = PIEZA_X[1] + 0.07
    vy0, vy1, vz0, vz1 = -1.05, 0.85, 0.8, 1.95
    gris = '#3a3d40'
    caja(x, (y0 + vy0) / 2, ALTO_PIEZA / 2, 0.14, vy0 - y0, ALTO_PIEZA, gris, 0.8)
    caja(x, (vy1 + y1) / 2, ALTO_PIEZA / 2, 0.14, y1 - vy1, ALTO_PIEZA, gris, 0.8)
    caja(x, (vy0 + vy1) / 2, vz0 / 2, 0.14, vy1 - vy0, vz0, gris, 0.8)
    caja(x, (vy0 + vy1) / 2, (vz1 + ALTO_PIEZA) / 2, 0.14, vy1 - vy0, ALTO_PIEZA - vz1, gris, 0.8)
    # Marco de aluminio.
    m = 0.04
    for cy, cz, sy, sz in [((vy0 + vy1) / 2, vz0, vy1 - vy0, m), ((vy0 + vy1) / 2, vz1, vy1 - vy0, m),
                           (vy0, (vz0 + vz1) / 2, m, vz1 - vz0), (vy1, (vz0 + vz1) / 2, m, vz1 - vz0)]:
        caja(x + 0.06, cy, cz, 0.05, sy, sz, '#8d9296', 0.35)
    # Repisa del lado de la sala de control.
    caja(x + 0.17, (vy0 + vy1) / 2, vz0 - 0.02, 0.3, vy1 - vy0 + 0.3, 0.03, '#55595d', 0.6)
    xv, m2 = PIEZA_X[1] + 0.14, 0.02
    vano = [Vector((xv, vy, vz)) for vy, vz in ((vy0 + m2, vz1 - m2), (vy1 - m2, vz1 - m2),
                                                (vy1 - m2, vz0 + m2), (vy0 + m2, vz0 + m2))]
    return ((vy0 + vy1) / 2, (vz0 + vz1) / 2), vano


def frazada(pose, colchon, alm, p):
    """Una frazada que cae sobre el cuerpo (tela simulada), doblada a la altura de la cintura."""
    c = CAMA
    arriba = c['cabeza_y'] - (0.62 if pose == 'supino' else 0.56)
    abajo = -c['largo'] / 2 - 0.12
    ancho = c['ancho'] + 0.5
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=72, y_subdivisions=84, size=1,
                                    location=(c['x'], (arriba + abajo) / 2, c['colchon'] + (0.32 if pose == 'supino' else 0.55)))
    f = bpy.context.object
    f.name = 'frazada'
    f.scale = (ancho, arriba - abajo, 1)
    bpy.ops.object.transform_apply(scale=True)
    for o in (colchon, alm, p.cuerpo, p.ropa):
        col = o.modifiers.new('choque', 'COLLISION')
        o.collision.thickness_outer = 0.02
        o.collision.cloth_friction = 40
    tela = f.modifiers.new('tela', 'CLOTH')
    s = tela.settings
    s.quality = 14
    s.mass = 0.6
    s.tension_stiffness = s.compression_stiffness = 25
    s.bending_stiffness = 6.0
    s.air_damping = 4
    tela.collision_settings.distance_min = 0.008
    tela.collision_settings.collision_quality = 4
    tela.collision_settings.use_self_collision = False
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, 42
    tela.point_cache.frame_end = 42
    for fr in range(1, 43):
        sc.frame_set(fr)
    activar(f)
    bpy.ops.object.modifier_apply(modifier='tela')
    sc.frame_set(1)
    for o in (colchon, alm, p.cuerpo, p.ropa):
        o.modifiers.remove(o.modifiers['choque'])
    so = f.modifiers.new('grosor', 'SOLIDIFY')
    so.thickness = 0.012
    sub = f.modifiers.new('sub', 'SUBSURF')
    sub.levels = sub.render_levels = 1
    bpy.ops.object.shade_smooth()
    m = bpy.data.materials.new('frazada')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.95
    # Tela a cuadros suaves.
    tex = nt.nodes.new('ShaderNodeTexChecker')
    tex.inputs['Scale'].default_value = 18
    tex.inputs['Color1'].default_value = (*[lineal(x) for x in hexa('#5f7d95')], 1)
    tex.inputs['Color2'].default_value = (*[lineal(x) for x in hexa('#56728a')], 1)
    nt.links.new(tex.outputs['Color'], b.inputs['Base Color'])
    poner(f, m)
    return f


# ── sensores de la polisomnografía ──────────────────────────────────────────


def faja(p, z, ancho=0.045, holgura=0.006):
    """Banda de esfuerzo (tórax o abdomen): sigue el contorno del cuerpo de pie a la altura z."""
    vs = [p.ropa.matrix_world @ v.co for v in p.ropa.data.vertices]
    vs += [p.cuerpo.matrix_world @ v.co for v in p.cuerpo.data.vertices]
    capa = [v for v in vs if abs(v.z - z) < 0.012 and abs(v.x) < 0.25]
    cx = sum(v.x for v in capa) / len(capa)
    cy = sum(v.y for v in capa) / len(capa)
    n = 48
    radios = [0.0] * n
    for v in capa:
        a = math.atan2(v.y - cy, v.x - cx)
        i = int((a + math.pi) / (2 * math.pi) * n) % n
        radios[i] = max(radios[i], math.hypot(v.x - cx, v.y - cy))
    for _ in range(3):   # suaviza y rellena huecos
        radios = [max(radios[i], (radios[i - 1] + radios[(i + 1) % n]) / 2) for i in range(n)]
    bm = bmesh.new()
    anillos = []
    for dz in (-ancho / 2, ancho / 2):
        fila = []
        for i in range(n):
            a = (i + 0.5) / n * 2 * math.pi - math.pi
            r = radios[i] + holgura
            fila.append(bm.verts.new((cx + r * math.cos(a), cy + r * math.sin(a), z + dz)))
        anillos.append(fila)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((anillos[0][i], anillos[0][j], anillos[1][j], anillos[1][i]))
    # El sensor de la faja, adelante (en la misma malla, así se mueve con ella).
    i_f = n // 4
    a = (i_f + 0.5) / n * 2 * math.pi - math.pi
    r = radios[i_f] + holgura + 0.006
    caja_ = bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((cx + r * math.cos(a), cy + r * math.sin(a), z))
                                  @ Matrix.Diagonal((0.05, 0.012, 0.032, 1)))
    for c in {f for v in caja_['verts'] for f in v.link_faces}:
        c.material_index = 1
    me = bpy.data.meshes.new('faja')
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new('faja', me)
    bpy.context.scene.collection.objects.link(o)
    # Pesos de los vértices del tronco más cercanos (solo huesos del tronco: si copia los del brazo,
    # la faja se va con él): se deforma con el tronco, como la polera.
    # (MakeHuman borra el cuerpo bajo la ropa: el tronco está en la polera.)
    puntos = []
    for src in (p.ropa, p.cuerpo):
        nombres = {g.index: g.name for g in src.vertex_groups}
        for v in src.data.vertices:
            pesos = {nombres[g.group]: g.weight for g in v.groups
                     if nombres[g.group].startswith(('spine', 'breast', 'pelvis'))}
            if sum(pesos.values()) > 0.3:
                puntos.append((src.matrix_world @ v.co, pesos))
    arbol = KDTree(len(puntos))
    for i, (co, _) in enumerate(puntos):
        arbol.insert(co, i)
    arbol.balance()
    for v in me.vertices:
        pesos = {}
        for _, i_c, _ in arbol.find_n(v.co, 6):
            for nm, w in puntos[i_c][1].items():
                pesos[nm] = pesos.get(nm, 0.0) + w
        total = sum(pesos.values())
        for nm, w in pesos.items():
            vg = o.vertex_groups.get(nm) or o.vertex_groups.new(name=nm)
            vg.add([v.index], w / total, 'REPLACE')
    o.parent = p.arm
    m = o.modifiers.new('esqueleto', 'ARMATURE')
    m.object = p.arm
    so = o.modifiers.new('grosor', 'SOLIDIFY')
    so.thickness = 0.004
    so.offset = 1
    activar(o)
    bpy.ops.object.shade_smooth()
    poner(o, mat('#202326', 0.75))
    o.data.materials.append(mat('#e8e8e8', 0.4))
    return o


def respiracion(p):
    """Shape keys 'torax' y 'abdomen' en el cuerpo, la polera y las fajas: cada punto del tronco se
    aleja del eje del cuerpo (más adelante que atrás). Por separado, para poder desfasarlos."""
    H = p.alto
    ys = {}
    # MakeHuman borra el cuerpo bajo la ropa: el tronco está en la polera.
    for o in (p.cuerpo, p.ropa):
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            if abs(w.x) < 0.17 and 0.45 * H < w.z < 0.85 * H:
                ys.setdefault(round(w.z * 100), []).append(w.y)
    eje_y = {k: (min(l) + max(l)) / 2 for k, l in ys.items()}
    REGION = {'torax': (0.63 * H, 0.80 * H, 0.020), 'abdomen': (0.52 * H, 0.665 * H, 0.026)}
    BRAZO = ('upperarm', 'lowerarm', 'wrist', 'finger', 'metacarpal')

    def campo(pt, region):
        z0, z1, amp = REGION[region]
        if not z0 < pt.z < z1:
            return Vector()
        k = round(pt.z * 100)
        yc = eje_y.get(k) or eje_y.get(k + 1) or eje_y.get(k - 1)
        if yc is None:
            return Vector()
        d = Vector((pt.x, pt.y - yc, 0))
        if d.length < 1e-6:
            return Vector()
        d.normalize()
        return d * amp * math.sin(math.pi * (pt.z - z0) / (z1 - z0)) * (0.25 + 0.75 * max(0.0, -d.y))

    p.respiran = [p.cuerpo, p.ropa, *p.fajas]
    for o in p.respiran:
        if not o.data.shape_keys:
            o.shape_key_add(name='Basis', from_mix=False)
        # Copia: agregar una shape key reubica las demás (una referencia a sus datos queda inválida).
        base = [kd.co.copy() for kd in o.data.shape_keys.key_blocks['Basis'].data]
        brazo = {g.index for g in o.vertex_groups if g.name.startswith(BRAZO)}
        libre = [1.0 - min(1.0, sum(g.weight for g in v.groups if g.group in brazo)) for v in o.data.vertices]
        inv = o.matrix_world.to_3x3().inverted()
        for region in REGION:
            k = o.shape_key_add(name=region, from_mix=False)
            for i, co in enumerate(base):
                if libre[i] > 0:
                    k.data[i].co = co + inv @ (campo(o.matrix_world @ co, region) * libre[i])


def curva(puntos, radio, color, nombre='cable'):
    cu = bpy.data.curves.new(nombre, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = radio
    cu.bevel_resolution = 3
    sp = cu.splines.new('NURBS')
    sp.points.add(len(puntos) - 1)
    for pt, xyz in zip(sp.points, puntos):
        pt.co = (*xyz, 1)
    sp.use_endpoint_u = True
    sp.order_u = 3
    o = bpy.data.objects.new(nombre, cu)
    bpy.context.scene.collection.objects.link(o)
    return poner(o, mat(color, 0.5))


def superficie(o):
    """BVH de la malla evaluada (con el cuerpo de pie), en coordenadas del mundo."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg)
    bm = bmesh.new()
    bm.from_mesh(ev.to_mesh())
    bm.transform(o.matrix_world)
    arbol = BVHTree.FromBMesh(bm)
    ev.to_mesh_clear()
    bm.free()
    return arbol


def sensores(p):
    """Fajas, cánula nasal, electrodos y oxímetro, montados con el cuerpo de pie (mirando a -y)."""
    H = p.alto
    p.fajas = [faja(p, 0.715 * H), faja(p, 0.605 * H)]
    piel = superficie(p.cuerpo)

    def pegado(pt, sobre=0.002):
        loc, normal, _, _ = piel.find_nearest(Vector(pt))
        return loc + normal * sobre, normal

    # Referencias de la cara.
    vs = [p.cuerpo.matrix_world @ v.co for v in p.cuerpo.data.vertices]
    cabeza = [v for v in vs if v.z > 0.86 * H]
    nariz = min(cabeza, key=lambda v: v.y)
    ojos = next(o for o in p.mallas if o.name.startswith('high-poly'))
    ov = [ojos.matrix_world @ v.co for v in ojos.data.vertices]
    ojo = {s: sum((v for v in ov if v.x * s > 0), Vector()) / sum(1 for v in ov if v.x * s > 0) for s in (1, -1)}
    oz = ojo[1].z
    oreja = {}
    for s in (1, -1):
        lado = [v for v in cabeza if v.x * s > 0.05 and oz - 0.045 < v.z < oz + 0.005]
        oreja[s] = max(lado, key=lambda v: v.x * s)
    frente = [v for v in cabeza if abs(v.x) < 0.012 and nariz.z - 0.13 < v.z < nariz.z - 0.05]
    menton = min(frente, key=lambda v: v.y)
    craneo = [v for v in cabeza if v.z > oz]
    centro = sum(craneo, Vector()) / len(craneo)
    centro.z = oz + 0.01
    tope = max(v.z for v in cabeza)
    # Donde se juntan los cables de los electrodos (arriba y atrás de la cabeza).
    nudo = Vector((0, centro.y + 0.05, tope + 0.005))

    def a_cabeza(o):
        a_hueso(o, p.arm, 'head')
        return o

    def electrodo(pt, normal, r=0.0065, color='#f4f4f4'):
        e = cil(pt.x, pt.y, pt.z, r, 0.003, color)
        e.rotation_euler = normal.to_track_quat('Z', 'Y').to_euler()
        return a_cabeza(e)

    def cable_a_nudo(pt, por=None):
        pts = [pt]
        if por is not None:
            pts.append(por)
        medio = (pts[-1] + nudo) / 2
        pts.append(centro + (medio - centro).normalized() * ((medio - centro).length + 0.015))
        pts.append(nudo)
        a_cabeza(curva([tuple(x) for x in pts], 0.0008, '#e8e8e8', 'hilo'))

    # Cánula nasal: de las narinas por las mejillas, sobre las orejas y se junta bajo el mentón.
    for s in (1, -1):
        o_ = oreja[s]
        pts = [Vector((s * 0.004, nariz.y + 0.012, nariz.z - 0.024)),
               pegado((s * 0.024, nariz.y + 0.014, nariz.z - 0.03), 0.004)[0],
               pegado((s * 0.055, ojo[s].y + 0.012, nariz.z - 0.02), 0.004)[0],
               pegado((s * (abs(o_.x) - 0.006), o_.y - 0.018, o_.z + 0.01), 0.004)[0],
               Vector((o_.x + s * 0.004, o_.y + 0.004, o_.z + 0.038)),
               Vector((o_.x - s * 0.002, o_.y + 0.03, o_.z - 0.005)),
               pegado((s * 0.05, o_.y + 0.005, menton.z + 0.005), 0.006)[0],
               Vector((s * 0.004, menton.y + 0.04, menton.z - 0.028))]
        a_cabeza(curva([tuple(x) for x in pts], 0.0021, '#d6e4ea', 'canula'))
    # EEG (sistema 10-20: frontal, centrales, occipitales) y mastoides.
    for d in [(0, -1, 0.45), (0.72, -0.05, 0.72), (-0.72, -0.05, 0.72), (0.32, 0.92, 0.2), (-0.32, 0.92, 0.2)]:
        d = Vector(d).normalized()
        hit = piel.ray_cast(centro, d)
        if hit[0] is not None:
            pt = hit[0] + hit[1] * 0.002
            electrodo(pt, hit[1])
            cable_a_nudo(pt)
    for s in (1, -1):
        pt, n = pegado((oreja[s].x - s * 0.012, oreja[s].y + 0.03, oreja[s].z - 0.035))
        electrodo(pt, n)
        cable_a_nudo(pt)
    # EOG: abajo y afuera del ojo izquierdo, arriba y afuera del derecho.
    for s, dz in ((1, -0.013), (-1, 0.013)):
        pt, n = pegado((ojo[s].x + s * 0.024, ojo[s].y + 0.008, ojo[s].z + dz))
        electrodo(pt, n, 0.0055)
        cable_a_nudo(pt, pegado((s * 0.075, oreja[s].y - 0.03, ojo[s].z + 0.03), 0.01)[0])
    # Mentón (EMG): dos bajo el labio y uno debajo.
    for x, dz in ((0.013, 0.0), (-0.013, 0.0), (0.0, -0.02)):
        pt, n = pegado((x, menton.y, menton.z + dz))
        electrodo(pt, n, 0.005)
        cable_a_nudo(pt, pegado((0.05 if x >= 0 else -0.05, oreja[1].y, menton.z + 0.01), 0.01)[0])
    p.coronilla = bpy.data.objects.new('coronilla', None)
    bpy.context.scene.collection.objects.link(p.coronilla)
    p.coronilla.location = nudo
    a_cabeza(p.coronilla)
    # Oxímetro en el índice derecho.
    dedo = p.hueso('finger2-2.R')
    ox_ = caja(dedo.x, dedo.y, dedo.z, 0.022, 0.03, 0.02, '#3a6fa3', 0.4, bisel=0.004, nombre='oximetro')
    a_hueso(ox_, p.arm, 'finger2-2.R')


def cables(p):
    """Del paquete de electrodos de la cabeza al cabezal del velador (ya con el paciente acostado)."""
    for o in getattr(p, 'cables', []):
        bpy.data.objects.remove(o, do_unlink=True)
    p.cables = []
    bpy.context.view_layer.update()
    cab = bpy.data.objects['cabezal'].location
    corona = p.coronilla.matrix_world.translation
    pts = [tuple(corona), (corona.x - 0.1, corona.y + 0.12, corona.z + 0.02),
           ((corona.x + cab.x) / 2, (corona.y + cab.y) / 2 + 0.1, CAMA['colchon'] + 0.15),
           (cab.x + 0.1, cab.y - 0.05, cab.z + 0.02), tuple(cab)]
    for i, (dx, dz) in enumerate([(0, 0), (0.008, 0.005), (-0.006, 0.008)]):
        p.cables.append(curva([(x + dx, y, z + dz) for x, y, z in pts], 0.0025,
                              ['#e04040', '#3060d0', '#f0f0f0'][i]))


# ── luces y cámaras ─────────────────────────────────────────────────────────


def luces():
    s = bpy.context.scene
    motores = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
    s.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in motores else 'BLENDER_EEVEE'
    s.view_settings.view_transform = 'AgX'
    s.view_settings.exposure = 0.0
    e = s.eevee
    e.use_shadows = True
    e.use_raytracing = True
    e.use_fast_gi = True
    e.taa_render_samples = 64
    w = bpy.data.worlds.new('w')
    s.world = w
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.02, 0.025, 0.035, 1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.4
    # Lámpara de noche (cálida) y una luz cenital tenue (fría).
    vx = CAMA['x'] - CAMA['ancho'] / 2 - 0.47
    bpy.ops.object.light_add(type='POINT', location=(vx, 1.02, 0.82))
    l = bpy.context.object
    l.data.energy = 45
    l.data.color = [lineal(c) for c in hexa('#ffbf80')]
    l.data.shadow_soft_size = 0.06
    bpy.ops.object.light_add(type='AREA', location=(0.1, -0.3, ALTO_PIEZA - 0.02))
    l = bpy.context.object
    l.data.energy = 60
    l.data.size = 1.2
    l.data.color = [lineal(c) for c in hexa('#c6d3ff')]


# Puntos de vista desde la sala de control (corrido a lo largo de la ventanilla, en metros): al mover
# el mouse LabSim pasa de uno a otro y el marco se corre más que la cama (sensación de profundidad).
VISTAS = (-0.32, -0.16, 0.0, 0.16, 0.32)
ANCHO_V, ALTO_V = 1280, 800
ANCHO_T, ALTO_T = 960, 720


def camara_ventanilla(centro_ventana, corrido=0.0):
    vy, vz = centro_ventana
    bpy.ops.object.camera_add(location=(PIEZA_X[1] + 1.05, vy - 0.12 + corrido, 1.62))
    cam = bpy.context.object
    cam.data.lens = 21
    mira = Vector((CAMA['x'], 0.0, CAMA['colchon'] + 0.15))
    cam.rotation_euler = (mira - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.name = f'cam_ventanilla{corrido:+.2f}'
    return cam


def camara_techo():
    bpy.ops.object.camera_add(location=(CAMA['x'] + 0.55, -0.3, ALTO_PIEZA - 0.08))
    cam = bpy.context.object
    cam.data.lens = 18
    mira = Vector((CAMA['x'], 0.0, CAMA['colchon']))
    cam.rotation_euler = (mira - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.name = 'cam_techo'
    return cam


def camara_cara(p):
    """Primer plano de la cara (solo para revisar el modelo)."""
    bpy.context.view_layer.update()
    cab = p.hueso('head')
    bpy.ops.object.camera_add(location=(cab.x + 0.45, cab.y - 0.35, cab.z + 0.35))
    cam = bpy.context.object
    cam.data.lens = 50
    cam.rotation_euler = (cab - cam.location).to_track_quat('-Z', 'Y').to_euler()
    return cam


# ── programa ────────────────────────────────────────────────────────────────


def vaciar():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()


def armar():
    vaciar()
    p = Paciente()
    sensores(p)
    respiracion(p)
    colchon, alm = pieza()
    centro, vano = ventanilla()
    luces()
    return p, colchon, alm, centro, vano


def foto(cam, w, h, ruta):
    s = bpy.context.scene
    s.camera = cam
    s.render.resolution_x, s.render.resolution_y = w, h
    s.render.filepath = str(ruta)
    bpy.ops.render.render(write_still=True)


def muestra(salida, pose='supino', despierto=False):
    salida = pathlib.Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    p, colchon, alm, centro, _ = armar()
    p.posar(pose)
    p.expresion('dormido')
    frazada(pose, colchon, alm, p)
    p.posar(pose, despierto)
    p.expresion(None if despierto else 'dormido')
    cables(p)
    fin = f'{pose}{"_despierto" if despierto else ""}'
    foto(camara_ventanilla(centro), ANCHO_V, ALTO_V, salida / f'ventanilla_{fin}.png')
    foto(camara_techo(), ANCHO_T, ALTO_T, salida / f'techo_{fin}.png')
    if os.environ.get('PSG_CARA'):
        foto(camara_cara(p), 800, 600, salida / f'cara_{fin}.png')


RESPIRA = 4     # niveles del tórax y del abdomen (0 = fin de la espiración, RESPIRA-1 = fin de la inspiración)
POSES_ORDEN = ('supino', 'izquierda', 'derecha')
BOCA = 0.8      # cuánto abre la boca al roncar
# Estados (clave pose_estado_tórax_abdomen):
#   0 dormido: la grilla entera de tórax × abdomen (en fase, paradoja de la apnea obstructiva, quieto);
#   1 despierto: respira en fase (la diagonal);
#   2 dormido roncando (boca abierta): en fase.


def estados():
    n = RESPIRA
    return ([(0, i, j) for i in range(n) for j in range(n)] + [(1, r, r) for r in range(n)]
            + [(2, r, r) for r in range(n)])


def todo(salida, poses=POSES_ORDEN):
    """Todos los cuadros: por pose y estado, la ventanilla desde cada punto de vista y la cámara del
    techo. Deja también vistas.json (dónde cae el vano de la ventanilla en cada punto de vista, para que
    LabSim ponga el reflejo del vidrio)."""
    salida = pathlib.Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    p, colchon, alm, centro, vano = armar()
    s = bpy.context.scene
    s.render.resolution_x, s.render.resolution_y = ANCHO_V, ALTO_V
    camaras = [camara_ventanilla(centro, c) for c in VISTAS]
    vanos = []
    for cam in camaras:
        vanos.append([[round(v.x * ANCHO_V, 1), round((1 - v.y) * ALTO_V, 1)]
                      for v in (world_to_camera_view(s, cam, q) for q in vano)])
    techo = camara_techo()
    (salida / 'vistas.json').write_text(json.dumps(
        {'vistas': list(VISTAS), 'vano': vanos, 'respira': RESPIRA,
         'ventanilla': [ANCHO_V, ALTO_V], 'techo': [ANCHO_T, ALTO_T]}, indent=1))
    for pose in poses:
        p.posar(pose)
        p.expresion('dormido')
        p.respirar(0, 0)
        f = frazada(pose, colchon, alm, p)
        for despierto in (False, True):
            p.posar(pose, despierto)
            cables(p)
            for e, i, j in estados():
                if (e == 1) != despierto:
                    continue
                p.expresion(None if despierto else 'dormido', BOCA if e == 2 else 0.0)
                p.respirar(i / (RESPIRA - 1), j / (RESPIRA - 1))
                clave = f'{pose}_{e}_{i}_{j}'
                for k, cam in enumerate(camaras):
                    foto(cam, ANCHO_V, ALTO_V, salida / f'v{k}_{clave}.png')
                foto(techo, ANCHO_T, ALTO_T, salida / f't_{clave}.png')
        bpy.data.objects.remove(f, do_unlink=True)
    (salida / 'fin.txt').write_text('ok')


if __name__ == '__main__':
    if ARGS and ARGS[0] == 'todo':
        todo(ARGS[1], ARGS[2:] or POSES_ORDEN)
    elif ARGS and ARGS[0] == 'muestra':
        muestra(ARGS[1], ARGS[2] if len(ARGS) > 2 else 'supino', len(ARGS) > 3 and ARGS[3] == 'despierto')
    else:
        print(__doc__)
