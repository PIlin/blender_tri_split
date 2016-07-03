import bpy
import mathutils
import bmesh

def deleteObject(obj):
    for sc in tuple(obj.users_scene):
        sc.objects.unlink(obj)

    objData = obj.data
    bpy.data.objects.remove(obj)
    bpy.data.meshes.remove(objData)


def deleteUnusedMeshes():
    for mesh in [m for m in bpy.data.meshes if m.users == 0]:
        bpy.data.meshes.remove(mesh)

class Plane:
    def __init__(self, n, p):
        self.n = n.normalized()
        self.p = p
        self.d = n.dot(p)


def joinBmeshes(bm1, bm2):
    print(len(bm1.verts), len(bm1.faces))
    tmpMesh = bpy.data.meshes.new('.tempMeshForJoin')
    bm2.to_mesh(tmpMesh)
    bm1.from_mesh(tmpMesh)
    print(len(bm1.verts), len(bm1.faces))
    bpy.data.meshes.remove(tmpMesh)








def testSplitLine(plane):
    bm = bmesh.new()

    print('plane n =', plane.n, ' plane.p =', plane.p, ' plane.d =', plane.d)

    A = mathutils.Vector((-1, 1, 0))
    B = mathutils.Vector((2, 0, 1))

    print('A =', A)
    print('B =', B)

    dA = plane.n.dot(A) - plane.d
    dB = plane.n.dot(B) - plane.d

    print('dA =', dA)
    print('dB =', dB)


    def classify(x):
        if x == 0: return 0
        elif x > 0: return 1
        return -1

    clA = classify(dA)
    clB = classify(dB)

    print('clA =', clA)
    print('clB =', clB)

    if (clA == 0) or (clB == 0) or (clA == clB):
        # points on same side of the plane, or on the plane
        vA = bm.verts.new(A)
        vB = bm.verts.new(B)
        bm.edges.new((vA, vB))
    else:
        X = A + (-dA / (dB - dA)) * (B - A)

        print('X =', X)

        vA = bm.verts.new(A)
        vB = bm.verts.new(B)
        vX = bm.verts.new(X)

        bm.edges.new((vA, vX))
        bm.edges.new((vX, vB))
        pass

    return bm


def classifyDV(x, eps=0):
    if x > eps: return 1
    elif x < -eps: return -1
    return 0
        
def buildFace(bm, verts):
    print('buildFace', verts)
    bverts = []
    for v in verts:
        bv = bm.verts.new(v)
        bverts.append(bv)

    return bm.faces.new(bverts)

def calcSplitPoint(A, B, dA, dB):
    return A + (-dA / (dB - dA)) * (B - A)


def splitFaceTwoPoints(verts, dverts, clVerts, outBm):
    print('splitFaceTwoPoints', verts, dverts, clVerts)
    for i in range(3):
        i1 = (i + 1) % 3
        i2 = (i + 2) % 3
        if (clVerts[i] != clVerts[i1]) and (clVerts[i] != clVerts[i2]):
            A = verts[i]
            dA = dverts[i]
            B = verts[i1]
            dB = dverts[i1]
            C = verts[i2]
            dC = dverts[i2]
            break

    X1 = calcSplitPoint(A, B, dA, dB)
    X2 = calcSplitPoint(A, C, dA, dC)

    vA = outBm.verts.new(A)
    vB = outBm.verts.new(B)
    vC = outBm.verts.new(C)
    vX1 = outBm.verts.new(X1)
    vX2 = outBm.verts.new(X2)

    outBm.faces.new((vA, vX1, vX2))
    outBm.faces.new((vX1, vB, vC))
    outBm.faces.new((vX1, vC, vX2))
    return

def splitFaceOnePoint(verts, dverts, clVerts, outBm):
    print('splitFaceOnePoint', verts, dverts, clVerts)
    for i in range(3):
        if clVerts[i] == 0:
            i1 = (i + 1) % 3
            i2 = (i + 2) % 3
            A = verts[i]
            dA = dverts[i]
            B = verts[i1]
            dB = dverts[i1]
            C = verts[i2]
            dC = dverts[i2]

    X = calcSplitPoint(B, C, dB, dC)

    vA = outBm.verts.new(A)
    vB = outBm.verts.new(B)
    vC = outBm.verts.new(C)
    vX = outBm.verts.new(X1)

    outBm.faces.new((vA, vB, vX))
    outBm.faces.new((vA, vX, vC))
    return


def splitFace(face, plane, outBm):
    verts = [v.co for v in face.verts]

    dverts = [0, 0, 0]
    clVerts = [0, 0, 0]
    sides = 0
    for i in range(3):
        V = verts[i]
        dV = plane.n.dot(V) - plane.d
        dverts[i] = dV

        clV = classifyDV(dV)
        clVerts[i] = clV

    countNeg = clVerts.count(-1)
    countPos = clVerts.count(1)
    countOnPlane = clVerts.count(0)

    print(verts, dverts, clVerts)

    assert(countNeg + countPos + countOnPlane == 3)

    if ((countNeg == 1) and (countPos == 2)) or ((countNeg == 2) and (countPos == 1)):
        splitFaceTwoPoints(verts, dverts, clVerts, outBm)
    elif (countOnPlane == 1) and (countPos == 1):
        splitFaceOnePoint(verts, dverts, clVerts, outBm)
    else:
        buildFace(outBm, verts)
    return




def splitObjectMesh(obj, plane):
    bm = bmesh.new()

    bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)
    bmesh.ops.triangulate(bm, faces=bm.faces)

    outBm = bmesh.new()

    print('source faces count =', len(bm.faces))

    for face in bm.faces:
        splitFace(face, plane, outBm)

    bm.free()

    print('result faces count =', len(outBm.faces))

    return outBm



def main():
    planeObjectName = 'PLANE'
    resultObjectName = 'RESULT'
    resultMeshName = resultObjectName + '_MESH'

    if resultObjectName in bpy.data.objects:
        deleteObject(bpy.data.objects[resultObjectName])

    resultMesh = bpy.data.meshes.new(resultMeshName)
    resultObj = bpy.data.objects.new(resultObjectName, resultMesh)
    bpy.context.scene.objects.link(resultObj)

    sc = bpy.context.scene

    #objects = bpy.context.selected_objects
    objects = sc.objects

    if not objects:
        print("No objects selected")
        return

    if planeObjectName in bpy.data.objects:
        planeObj = bpy.data.objects[planeObjectName]

        print('mesh plane norm', planeObj.data.polygons[0].normal)
        n = planeObj.matrix_world.to_quaternion() * mathutils.Vector(planeObj.data.polygons[0].normal)
        p = mathutils.Vector(planeObj.matrix_world.translation)
        print('found plane', n, p)
        splitPlane = Plane(n, p)
    else:
        splitPlane = Plane(mathutils.Vector((1, 0, 0)), mathutils.Vector((0.33, 1, 1)))

    tmpResultBMesh = bmesh.new()

    for obj in objects:
        if obj.name == resultObj.name:
            continue
        if obj.name == planeObjectName:
            continue
        if obj.type != 'MESH':
            continue

        print(obj.name)

        bm = splitObjectMesh(obj, splitPlane)
        joinBmeshes(tmpResultBMesh, bm)
        bm.free()

    # bm = testSplitLine(splitPlane)
    # joinBmeshes(tmpResultBMesh, bm)
    # bm.free()

    tmpResultBMesh.to_mesh(resultMesh)
    tmpResultBMesh.free()

    sc.update()






main()