#!/usr/bin/env python
#
# Script to convert a mesh from Gmsh to Cardiax XML format
# Gmsh element types
# 1: 2-node line.
# 2: 3-node triangle.
# 3: 4-node quadrangle.
# 4: 4-node tetrahedron.
# 5: 8-node hexahedron.
# 6: 6-node prism.
# 7: 5-node pyramid.
#
# Bernardo M. Rocha, 2015
#
import sys, time, os
import numpy as np

gmsh_etype_dim = {'1': 1, '2': 2, '3': 2, '4': 3, '5': 3}

def gmsh2xml (gmshMesh, outputMesh, materialProperties, markers_boundbox, PVloopParams, PVloopFile=None):

    xmlfilename = outputMesh

    # read header from .msh file
    f = open(gmshMesh)
    line = f.readline() # $MeshFormat
    line = f.readline() # $2.1 0 8
    line = f.readline() # $EndMeshFormat

    # read nodes and write .pts file
    line = f.readline() # $Node
    line = f.readline() # num_node
    num_nodes = int(line)
    pts = np.zeros((num_nodes,3))
    for i in range(num_nodes):
        line = f.readline().split(" ")
        node_id = int(line[0])
        x, y, z = float(line[1]), float(line[2]), float(line[3])
        pts[i,0] = x
        pts[i,1] = y
        pts[i,2] = z

    line = f.readline() # $EndNodes
    print("Reading nodes...done")

    # read elements and
    line = f.readline() # $Elements
    line = f.readline() # num_elements

    num_elements = int(line)
    elements = 0
    elems = []
    elem_types = []
    elem_marker = []

    for i in range(num_elements):
        line = f.readline().split(" ")
        elem_id = int(line[0])
        elem_type = int(line[1])
        elem_types.append(elem_type)

        if (elem_type == 1): #line
            elements = elements + 1
            num_tags = int(line[2])
            tags = []
            for j in range(num_tags):
                tags.append(int(line[3+j]))
            n1 = int(line[3+num_tags])
            n2 = int(line[4+num_tags])
            elems.append( (n1,n2) )
            #print("marker %d" % tags[0] )
            #print(tags)
            elem_marker.append( tags[0] )
        elif (elem_type == 2): # triangle
            elements = elements + 1
            num_tags = int(line[2])
            tags = []
            for j in range(num_tags):
                tags.append(int(line[3+j]))
            n1 = int(line[3+num_tags])
            n2 = int(line[4+num_tags])
            n3 = int(line[5+num_tags])
            elems.append( (n1,n2,n3) )
            #print("marker %d" % tags[0])
            elem_marker.append( tags[0] )
            #felem.write("Tr %d %d %d 1\n" % (n1,n2,n3))
        elif (elem_type == 3): # quad
            elements = elements + 1
            num_tags = int(line[2])
            tags = []
            for j in range(num_tags):
                tags.append(int(line[3+j]))
            n1 = int(line[3+num_tags])
            n2 = int(line[4+num_tags])
            n3 = int(line[5+num_tags])
            n4 = int(line[6+num_tags])
            elems.append( (n1,n2,n3,n4) )
            #print("marker %d" % tags[0] )
            elem_marker.append( tags[0] )
            #felem.write("Tr %d %d %d 1\n" % (n1,n2,n3))
        elif (elem_type == 5): # hexahedra
            elements = elements + 1
            num_tags = int(line[2])
            tags = []
            for j in range(num_tags):
                tags.append(int(line[3+j]))
            n1 = int(line[3+num_tags])
            n2 = int(line[4+num_tags])
            n3 = int(line[5+num_tags])
            n4 = int(line[6+num_tags])
            n5 = int(line[7+num_tags])
            n6 = int(line[8+num_tags])
            n7 = int(line[9+num_tags])
            n8 = int(line[10+num_tags])
            elems.append( (n1,n2,n3,n4,n5,n6,n7,n8) )
            elem_marker.append( tags[-2] )
        elif (elem_type == 4): # tetrahedra
            elements = elements + 1
            num_tags = int(line[2])
            tags = []
            for j in range(num_tags):
                tags.append(int(line[3+j]))
            #print(tags[-2])
            n1 = int(line[3+num_tags])
            n2 = int(line[4+num_tags])
            n3 = int(line[5+num_tags])
            n4 = int(line[6+num_tags])
            t = (n1,n2,n4,n3)
            elems.append( t )
            elem_marker.append( tags[0] )

    line = f.readline() # $EndElements
    f.close()

    # make some considerations
    # gmsh element type 1-line, 2-tri, 3-quad, 4-tet, 5-hex, ....
    elem_type = np.array(elem_types).max()
    if (elem_type <= 1 or elem_type > 5):
        print("Error: element type is not supported")
        sys.exit(1)

    # find out dimension
    num_dim = 1
    if (elem_type == 2 or elem_type == 3):   num_dim = 2
    elif (elem_type == 4 or elem_type == 5): num_dim = 3

    # read boundary elements section
    selem = []
    velem = []
    selem_markers = []

    for i in xrange(num_elements):
        etype = int(elem_types[i])
        eskey = str(etype)
        eldim = gmsh_etype_dim[eskey]
        marker = elem_marker[i]

        # then it is a boundary element
        if(eldim < num_dim):
            selem.append( np.array(elems[i][:],dtype=int) )
            selem_markers.append( elem_marker[i] )
        else:
            velem.append( np.array(elems[i][:],dtype=int) )

    num_elements = len(velem)
    num_boundary_elem = len(selem)

    print("Reading elements...done.")

    elem_xml = "line"
    if(elem_type == 2):
        elem_xml = "triangle"
    elif(elem_type == 3):
        elem_xml = "quadrilateral"
    elif(elem_type == 4):
        elem_xml = "tetrahedron"
    elif(elem_type == 5):
        elem_xml = "hexahedron"

    # print info
    print("Number of dimensions: %d" % num_dim)
    print("Number of nodes: %d" % num_nodes)
    print("Number of elements: %d" % num_elements)
    print("Number of boundary elements: %d" % num_boundary_elem)
    print("Element type: %s" % elem_xml)

    #
    # start writing the output file
    #

    # basic header
    outputFile = file(outputMesh, 'w')

    endo_indices = []
    for i in range(len(selem)):
        if selem_markers[i] == 30:
            endo_indices.append(selem[i][:] - 1)

    endoPoints = np.unique(endo_indices)

    np.savetxt('endo_indices.txt', endoPoints, fmt='%d')


    base_indices = []
    for i in range(len(selem)):
        if selem_markers[i] == 10:
            base_indices.append(selem[i][:] - 1)

    epi_indices = []
    for i in range(len(selem)):
        if selem_markers[i] == 50:
            epi_indices.append(selem[i][:] - 1)            

    prescDispl = np.unique(base_indices)
    prescDisplEPI = np.unique(epi_indices)

    print 'Fixed nodes:'
    print prescDispl
    print prescDisplEPI
    #problemtyp = 'THREE_DIM'


    if(len(prescDispl) > 0):
        if(materialProperties['problemtyp'] is not None):
            outputFile.write('<elasticity type="%s">\n' % materialProperties['problemtyp'])
            outputFile.write('  <parameters>\n')
            outputFile.write('  <material>%s</material>\n' % materialProperties['material_type'])
            outputFile.write('    <coefficients>%s</coefficients>\n' % str(materialProperties['material_coef']).replace('[','').replace(']',''))
            outputFile.write('    <ninc>%d</ninc>\n' % materialProperties['num_increments'])
            outputFile.write('  </parameters>\n')
            outputFile.write('  <pressure>\n')
            outputFile.write('    <node id="1" marker="%d" value="%f"/>\n' % (materialProperties['pressure_marker'], materialProperties['pressure_value']))
            outputFile.write('  </pressure>\n')

        else:
            outputFile.write('<elasticity>\n')

        outputFile.write('  <prescribed_displacement>\n')
        for i in range(len(prescDispl)):
            #node,d,v = prescDispl[i]
            #outputFile.write('    <node id="%d" direction="%d" value="%f" />\n' % (node,d,v))
            
            node = prescDispl[i]
            outputFile.write('    <node id="%d" direction="%d" value="%f" />\n' % (node,0,0))
            outputFile.write('    <node id="%d" direction="%d" value="%f" />\n' % (node,1,0))
            outputFile.write('    <node id="%d" direction="%d" value="%f" />\n' % (node,2,0))

        for i in range(len(prescDisplEPI)):
        
            node = prescDisplEPI[i]
            #outputFile.write('    <node id="%d" direction="%d" value="%f" />\n' % (node,0,0))
            #outputFile.write('    <node id="%d" direction="%d" value="%f" />\n' % (node,1,0))
            #outputFile.write('    <node id="%d" direction="%d" value="%f" />\n' % (node,2,0))


        outputFile.write('  </prescribed_displacement>\n')
        outputFile.write('</elasticity>\n')

    # write mesh
    outputFile.write('<mesh celltype="%s" dim="%d">\n' % (elem_xml, num_dim))

    # nodes section
    outputFile.write('  <nodes size="%d">\n' % (num_nodes))
    for i in xrange(num_nodes):
        outputFile.write('    <node id="%d" ' % (i) )
        outputFile.write('x="%f" y="%f" z="%f" />\n' % (pts[i,0],pts[i,1],pts[i,2]))
    outputFile.write('  </nodes>\n')

    # elements section
    outputFile.write('  <elements size="%d">\n' % (num_elements))
    
    #boundbox = np.loadtxt('markers_boundbox.txt')

    for i in xrange(len(velem)):
        #etype = int(elem_types[i])
        #eskey = str(etype)
        #eldim = gmsh_etype_dim[eskey]
        # then it is a boundary element
        #if(eldim < num_dim):
        #    boundary.append( np.array(elems[i][:],dtype=int)-1 )
#        mark = get_marker(pts, velem[i][:], markers_boundbox)
        outputFile.write('    <element id="%d" marker="%d" ' % (i, 0))
        write_element(outputFile, velem[i][:] )
    outputFile.write('  </elements>\n')


    # reading fibers
    fibFile = outputMesh.replace('_cardiax.xml', '.lon')
    if( os.path.isfile(fibFile) ):
        print("Reading fibers from %s" % fibFile)
        fvec = open(fibFile,"r")
        fibtype = int(fvec.readline())
        fibname = None
        fvec.close()    
        vecs = np.loadtxt(fibFile, skiprows=1)
        fibsize = np.shape(vecs)[0]
        if(fibsize != num_elements):
            print("Error: number of fiber vectors must match the number of elements")
            sys.exit(1)
        if(fibtype==1):
            fibname = "fiber_transversely_isotropic"
        else:
            fibname = "fiber_orthotropic"
        print("Fiber model: %s" % fibname)
        print("Fiber vectors: %d" % fibsize)

        # element_data section
        outputFile.write('  <element_data type="%s">\n' % (fibname))
        for i in xrange(fibsize):
            outputFile.write('    <element id="%d">\n' % (i))
            write_vecs(outputFile, vecs[i,:])
            outputFile.write('    </element>\n')
        outputFile.write('  </element_data>\n')     



    if(PVloopFile is not None):

        pvloopFile = open(PVloopFile, 'r')

        line = pvloopFile.readline()
        l = line.split()
        outputFile.write('  <pvloop size="%s" total_time="%s" C_art="%f" R_per="%f" P_o="%f" p_art="%f" stroke_volume="%f" >\n' % (l[0], l[1], PVloopParams['C_art'], PVloopParams['R_per'], PVloopParams['P_o'], PVloopParams['p_art'], PVloopParams['stroke_volume'] ))
        size = int(l[0])


        for i in xrange(size):
           line = pvloopFile.readline() 
           l = line.split()
           outputFile.write('    <step time="%s" pressure="%s" active_tension="%s" />\n' % (l[0],l[1],l[2]))
       
        outputFile.write('  </pvloop>\n')

    # boundary section
    # first find type of boundary element
    # then write to file
    if(elem_type == 3): belem_xml = "line"
    elif(elem_type == 4): belem_xml = "triangle"
    elif(elem_type == 5): belem_xml = "quadrilateral"

    outputFile.write('  <boundary celltype="%s" dim="%d">\n' % (belem_xml,num_dim-1))
    k=0
    for i in range(len(selem)):
        if(selem_markers[i]==30):
            outputFile.write('    <element id="%d" marker="%d" ' % (k,selem_markers[i]))
            write_element(outputFile, selem[i][:] )
            k+=1
    outputFile.write('  </boundary>\n')

    outputFile.write('</mesh>\n')
    outputFile.close()
    print("Done")

# ------------------------------------------------------------------------------

def write_element(out, conec):
    num_nodes = len(conec)
    for i in range(num_nodes):
        out.write('v%d="%d" ' % (i,conec[i]-1))
    out.write('/>\n')

# ------------------------------------------------------------------------------

def get_marker(coord, indices, boundbox):
    xc = (coord[indices[0]-1, 0] + coord[indices[1]-1, 0] + coord[indices[2]-1, 0] + coord[indices[3]-1, 0])/4.0 
    yc = (coord[indices[0]-1, 1] + coord[indices[1]-1, 1] + coord[indices[2]-1, 1] + coord[indices[3]-1, 1])/4.0 
    zc = (coord[indices[0]-1, 2] + coord[indices[1]-1, 2] + coord[indices[2]-1, 2] + coord[indices[3]-1, 2])/4.0
    zf17 = boundbox[-1, -1]
    for i in range(17):
        #m, xi, yi, zi, xf, yf, zf = boundbox[i]
        m, x1, y1, z1, x2, y2, z2 = boundbox[i]

        A = np.array([0.0,0.0,z1])
        B = np.array([2.*x1, 2.*y1, z1])
        C = np.array([2.*x2, 2.*y2, z1])
        P = np.array([xc, yc, zc])

        #Compute vectors        
        v0 = C - A
        v1 = B - A
        v2 = P - A

        #Barycentric Technique for point inside triangle, described in http://blackpawn.com/texts/pointinpoly/
        #Compute dot products
        dot00 = np.dot(v0, v0)
        dot01 = np.dot(v0, v1)
        dot02 = np.dot(v0, v2)
        dot11 = np.dot(v1, v1)
        dot12 = np.dot(v1, v2)

        #Compute barycentric coordinates
        invDenom = 1.0 / (dot00 * dot11 - dot01 * dot01)
        u = (dot11 * dot02 - dot01 * dot12) * invDenom
        v = (dot00 * dot12 - dot01 * dot02) * invDenom

        #Check if point is in triangle
        #if ( (xc >= xi and xc <= xf) and (yc >= yi and yc <= yf) and (zc >= zi and zc <= zf) ):
        if (u >= 0) and (v >= 0) and (u + v < 1) and (zc >= z1 and zc <= z2):
            if i == 16:
                return 12
            else:
                return m 
        elif (zc > zf17):
            return 16

    return 0




# ------------------------------------------------------------------------------

def write_vecs(out, vec):
    size = np.shape(vec)[0]
    # transversely isotropic - fiber only
    if(size == 3):
        out.write('        <fiber>%f,%f,%f</fiber>\n' % (vec[0],vec[1],vec[2]))
    elif(size == 9):
        out.write('        <fiber>%f,%f,%f</fiber>\n' % (vec[0],vec[1],vec[2]))
        out.write('        <sheet>%f,%f,%f</sheet>\n' % (vec[3],vec[4],vec[5]))
        out.write('        <normal>%f,%f,%f</normal>\n' % (vec[6],vec[7],vec[8]))
        # TERMINAR DE IMPLEMENTAR
        pass

# ------------------------------------------------------------------------------

if __name__ == "__main__":

    if (len(sys.argv) < 3):
        print("\n Usage: gmsh2xml <gmsh_mesh> <output_xml> [parameters.par]\n")
        sys.exit(-1)

    # parse and check input
    gmsh_mesh = sys.argv[1]

    if (not os.path.isfile(gmsh_mesh)):
       print("\n Error: the input gmsh %s does not exist.\n" % (gmsh_mesh))
       sys.exit(-1)

    par = None
    if(len(sys.argv) == 4):
        par = sys.argv[3]

    # convert
    gmsh2xml(sys.argv[1], sys.argv[2], par)

# end of main
