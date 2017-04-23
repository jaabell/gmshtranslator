from __future__ import print_function
import scipy as sp
import sys

class gmshTranslator:
    """
gmshTranslator

    Class that takes an input gmsh file (.msh) and provides functionality to parse and transform
    the .msh to other formats. 
    """



####################################################################################################
####################################################################################################
    def __init__(self, mshfilename):

        self.mshfilename = mshfilename
        self.mshfid = open(mshfilename,"r")

        #Initially, parse elements to know what nodes are in which physical groups.
        reading_nodes = 0
        reading_elements = 0

        self.__inform__("Initializing...")

        self.Nnodes = 0
        self.Nelem = 0
        self.physical_groups = []
        self.nodes_in_physical_groups = {}

        linenumber = 1
        for line in self.mshfid:
            #################################################
            # Identify begining of nodes and elements sections
            if line.find("$Nodes") >= 0:
                reading_nodes = 1
                continue
            
            if line.find("$Elements") >= 0:
                reading_elements = 1
                continue    
            #################################################    

            #################################################
            #Identify end of nodes and element sections
            if line.find("$EndElements") >= 0:
                reading_elements = 0
                continue
            if line.find("$EndNodes") >= 0:
                reading_nodes  = 0
                continue
            #################################################
        
            #If this is the first line of nodes, read the number of nodes. 
            if reading_nodes == 1:
                self.Nnodes = sp.int32(line)
                self.__inform__("Mesh has " + str(self.Nnodes) + " nodes.")
                reading_nodes = 2
                continue
            
            #If this is the first line of elements, read the number of elements
            if reading_elements == 1:
                self.Nelem = sp.int32(line)
                self.__inform__("Mesh has " + str(self.Nelem) + " elements.")
                reading_elements = 2
                continue

            #Now parse elements and populate the list of nodes in groups
            if reading_elements == 2:
                sl = sp.array( line.split(), dtype = sp.int32)
                
                eletag = sl[0]
                eletype = sl[1]
                ntags = sl[2]
                physgrp = 0
                partition = 0

                if ntags >= 2:
                    physgrp = sl[3]
                    nodelist = sl[(3 + ntags)::]

                    # sys.stdout.write(str(nodelist.size) + " ")

                    if physgrp in self.physical_groups:
                        self.nodes_in_physical_groups[physgrp][nodelist] = 1
                    else:
                        self.nodes_in_physical_groups[physgrp] = -sp.ones(self.Nnodes+1, dtype=sp.int16)
                        self.nodes_in_physical_groups[physgrp][nodelist] = 1
                        self.physical_groups.append(physgrp)
                        pass
                else:
                    self.__error__(".msh file has < 2 tags at line " + str(linenumber))

            linenumber += 1
        #end for line
        self.__inform__("Processed " + str(linenumber) +" lines.")
        self.__inform__("There are " + str(len(self.physical_groups)) + " physical groups available: ")
        for g in self.physical_groups:
            self.__inform__("     > " + str(g))


        self.nodes_rules = []
        self.elements_rules = []
    #end def __init__

        self.mshfid.close()


####################################################################################################
####################################################################################################

    def __del__(self):
        self.mshfid.close()
        self.__inform__("Ending")




####################################################################################################
####################################################################################################
    def add_elements_rule(self, condition, action):
        self.elements_rules.append((condition, action))
        pass




####################################################################################################
####################################################################################################
    def add_nodes_rule(self, condition, action):
        self.nodes_rules.append((condition, action))
        pass


####################################################################################################
####################################################################################################
    def clear_rules(self):
        self.nodes_rules = []
        self.elements_rules = []
        pass






####################################################################################################
####################################################################################################
    def parse(self):
        self.mshfid = open(self.mshfilename, 'r')


        #Advance to nodes
        line = self.mshfid.readline()
        while(line.find("$Nodes") < 0):
            line = self.mshfid.readline()
            pass
        line = self.mshfid.readline()  #This line should contain number of nodes

        #Check that number of nodes in file is still the number of nodes in memory
        if(not sp.int32(line) == self.Nnodes):
            self.__error__("Something wrong. Aborting.")
            exit(-1)

        self.__inform__("Parsing nodes")

        if len(self.nodes_rules) == 0:
            self.__inform__("No rules for nodes... skipping nodes.")
            for i in range(self.Nnodes):
                self.mshfid.readline()
        else:
            #Read all nodes and do stuff
            for i in range(self.Nnodes):

                #Parse the line
                sl = self.mshfid.readline().split()
                tag = sp.int32(sl[0])
                x = sp.double(sl[1])
                y = sp.double(sl[2])
                z = sp.double(sl[3])

                #Figure out the groups to which this node belongs
                physgroups = []
                for grp in self.physical_groups:
                    if self.nodes_in_physical_groups[grp][tag] == 1:
                        physgroups.append(grp)

                for condition, action in self.nodes_rules:
                    if condition(tag,x,y,z,physgroups):
                        action(tag,x,y,z)
                    pass

        #Read another 2 lines after nodes are done. This should be $Elements
        line = self.mshfid.readline()
        line = self.mshfid.readline()
        if(line.find("$Elements") == 0):
            self.__inform__("Parsing elements")
        else:
            self.__error__("Something wrong reading elements. ")
            exit(-1)

        line = self.mshfid.readline()  #This line should contain number of elements

        #Check that number of elements in file is still the number of elements in memory
        if(not sp.int32(line) == self.Nelem):
            self.__error__("Something wrong. Aborting.")
            exit(-1)


        if len(self.elements_rules) == 0:
            self.__inform__("No rules for elements... skipping elements.")
            for i in range(self.Nelem):
                self.mshfid.readline()
        else:
            #Read all elements and do stuff
            nodes = []
            for i in range(self.Nelem):

                sl = self.mshfid.readline().split()

                #Parse the line
                eletag = sp.int32(sl[0])
                eletype = sp.int32(sl[1])
                ntags = sp.int32(sl[2])
                physgrp = sp.int32(sl[3])
                partition = sp.int32(sl[4])

                if ntags >= 2:
                    physgrp = sp.int32(sl[3])
                    nodes = sp.array(sl[(3 + ntags)::], dtype=sp.int32)
            
                    for condition, action in self.elements_rules:
                        if condition(eletag,eletype,physgrp,nodes):
                            action(eletag,eletype,physgrp,nodes)
                        pass
                else:
                    self.__error__(".msh file has < 2 tags element with tag " + str(eletag))


        pass





####################################################################################################
####################################################################################################
    def __inform__(self, msg):
        print ("gmshTranslator: " + msg)



####################################################################################################
####################################################################################################
    def __error__(self, msg):
        sys.stderr.write("gmshTranslator: ERROR! -> " + msg + "\n")

    #GMSH element definitions
    line_2_node                 = sp.int32(1)  # 2-node line.
    triangle_3_node             = sp.int32(2)  # 3-node triangle.
    quadrangle_4_node           = sp.int32(3)  # 4-node quadrangle.
    tetrahedron_4_node          = sp.int32(4)  # 4-node tetrahedron.
    hexahedron_8_node           = sp.int32(5)  # 8-node hexahedron.
    prism_6_node                = sp.int32(6)  # 6-node prism.
    pyramid_5_node              = sp.int32(7)  # 5-node pyramid.
    line_3_node                 = sp.int32(8)  # 3-node second order line (2 nodes associated with the vertices and 1 with the edge).
    triangle_6_node             = sp.int32(9)  # 6-node second order triangle (3 nodes associated with the vertices and 3 with the edges).
    quadrangle_9_node           = sp.int32(10) # 9-node second order quadrangle (4 nodes associated with the vertices, 4 with the edges and 1 with the face).
    tetrahedron_10_node         = sp.int32(11) # 10-node second order tetrahedron (4 nodes associated with the vertices and 6 with the edges).
    hexahedron_27_node          = sp.int32(12) # 27-node second order hexahedron (8 nodes associated with the vertices, 12 with the edges, 6 with the faces and 1 with the volume).
    prism_18_node               = sp.int32(13) # 18-node second order prism (6 nodes associated with the vertices, 9 with the edges and 3 with the quadrangular faces).
    pyramid_14_node             = sp.int32(14) # 14-node second order pyramid (5 nodes associated with the vertices, 8 with the edges and 1 with the quadrangular face).
    point_1_node                = sp.int32(15) # 1-node point.
    quadrangle_8_node           = sp.int32(16) # 8-node second order quadrangle (4 nodes associated with the vertices and 4 with the edges).
    hexahedron_20_node          = sp.int32(17) # 20-node second order hexahedron (8 nodes associated with the vertices and 12 with the edges).
    prism_15_node               = sp.int32(18) # 15-node second order prism (6 nodes associated with the vertices and 9 with the edges).
    pyramid_13_node             = sp.int32(19) # 13-node second order pyramid (5 nodes associated with the vertices and 8 with the edges).
    triangle_9_node_incomplete  = sp.int32(20) # 9-node third order incomplete triangle (3 nodes associated with the vertices, 6 with the edges)
    triangle_10_node            = sp.int32(21) # 10-node third order triangle (3 nodes associated with the vertices, 6 with the edges, 1 with the face)
    triangle_12_node_incomplete = sp.int32(22) # 12-node fourth order incomplete triangle (3 nodes associated with the vertices, 9 with the edges)
    triangle_15_node            = sp.int32(23) # 15-node fourth order triangle (3 nodes associated with the vertices, 9 with the edges, 3 with the face)
    triangle_15_node_incomplete = sp.int32(24) # 15-node fifth order incomplete triangle (3 nodes associated with the vertices, 12 with the edges)
    triangle_21_node            = sp.int32(25) # 21-node fifth order complete triangle (3 nodes associated with the vertices, 12 with the edges, 6 with the face)
    edge_4_node                 = sp.int32(26) # 4-node third order edge (2 nodes associated with the vertices, 2 internal to the edge)
    edge_5_node                 = sp.int32(27) # 5-node fourth order edge (2 nodes associated with the vertices, 3 internal to the edge)
    edge_6_node                 = sp.int32(28) # 6-node fifth order edge (2 nodes associated with the vertices, 4 internal to the edge)
    tetrahedron_20_node         = sp.int32(29) # 20-node third order tetrahedron (4 nodes associated with the vertices, 12 with the edges, 4 with the faces)
    tetrahedron_35_node         = sp.int32(30) # 35-node fourth order tetrahedron (4 nodes associated with the vertices, 18 with the edges, 12 with the faces, 1 in the volume)
    tetrahedron_56_node         = sp.int32(31) # 56-node fifth order tetrahedron (4 nodes associated with the vertices, 24 with the edges, 24 with the faces, 4 in the volume)
    hexahedron_64_node          = sp.int32(92) # 64-node third order hexahedron (8 nodes associated with the vertices, 24 with the edges, 24 with the faces, 8 in the volume)
    hexahedron_125_node         = sp.int32(93) # 125-node fourth order hexahedron (8 nodes associated with the vertices, 36 with the edges, 54 with the faces, 27 in the volume)



#end class gmshtranslator


# From GMSH doc - 
# 1  : 2-node line.
# 2  : 3-node triangle.
# 3  : 4-node quadrangle.
# 4  : 4-node tetrahedron.
# 5  : 8-node hexahedron.
# 6  : 6-node prism.
# 7  : 5-node pyramid.
# 8  : 3-node second order line (2 nodes associated with the vertices and 1 with the edge).
# 9  : 6-node second order triangle (3 nodes associated with the vertices and 3 with the edges).
# 10 : 9-node second order quadrangle (4 nodes associated with the vertices, 4 with the edges and 1 with the face).
# 11 : 10-node second order tetrahedron (4 nodes associated with the vertices and 6 with the edges).
# 12 : 27-node second order hexahedron (8 nodes associated with the vertices, 12 with the edges, 6 with the faces and 1 with the volume).
# 13 : 18-node second order prism (6 nodes associated with the vertices, 9 with the edges and 3 with the quadrangular faces).
# 14 : 14-node second order pyramid (5 nodes associated with the vertices, 8 with the edges and 1 with the quadrangular face).
# 15 : 1-node point.
# 16 : 8-node second order quadrangle (4 nodes associated with the vertices and 4 with the edges).
# 17 : 20-node second order hexahedron (8 nodes associated with the vertices and 12 with the edges).
# 18 : 15-node second order prism (6 nodes associated with the vertices and 9 with the edges).
# 19 : 13-node second order pyramid (5 nodes associated with the vertices and 8 with the edges).
# 20 : 9-node third order incomplete triangle (3 nodes associated with the vertices, 6 with the edges)
# 21 : 10-node third order triangle (3 nodes associated with the vertices, 6 with the edges, 1 with the face)
# 22 : 12-node fourth order incomplete triangle (3 nodes associated with the vertices, 9 with the edges)
# 23 : 15-node fourth order triangle (3 nodes associated with the vertices, 9 with the edges, 3 with the face)
# 24 : 15-node fifth order incomplete triangle (3 nodes associated with the vertices, 12 with the edges)
# 25 : 21-node fifth order complete triangle (3 nodes associated with the vertices, 12 with the edges, 6 with the face)
# 26 : 4-node third order edge (2 nodes associated with the vertices, 2 internal to the edge)
# 27 : 5-node fourth order edge (2 nodes associated with the vertices, 3 internal to the edge)
# 28 : 6-node fifth order edge (2 nodes associated with the vertices, 4 internal to the edge)
# 29 : 20-node third order tetrahedron (4 nodes associated with the vertices, 12 with the edges, 4 with the faces)
# 30 : 35-node fourth order tetrahedron (4 nodes associated with the vertices, 18 with the edges, 12 with the faces, 1 in the volume)
# 31 : 56-node fifth order tetrahedron (4 nodes associated with the vertices, 24 with the edges, 24 with the faces, 4 in the volume)
# 92 : 64-node third order hexahedron (8 nodes associated with the vertices, 24 with the edges, 24 with the faces, 8 in the volume)
# 93 : 125-node fourth order hexahedron (8 nodes associated with the vertices, 36 with the edges, 54 with the faces, 27 in the volume)

# Line:                   Line3:           Line4:    
                                                
# 0----------1 --> u      0-----2----1     0----2----3----1

# Triangle:               Triangle6:          Triangle9/10:          Triangle12/15:

# v                                                              
# ^                                                                   2 
# |                                                                   | \ 
# 2                       2                    2                      9   8
# |`\                     |`\                  | \                    |     \ 
# |  `\                   |  `\                7   6                 10 (14)  7
# |    `\                 5    `4              |     \                |         \ 
# |      `\               |      `\            8  (9)  5             11 (12) (13) 6
# |        `\             |        `\          |         \            |             \
# 0----------1 --> u      0-----3----1         0---3---4---1          0---3---4---5---1

# Quadrangle:            Quadrangle8:            Quadrangle9:

#       v
#       ^
#       |
# 3-----------2          3-----6-----2           3-----6-----2 
# |     |     |          |           |           |           | 
# |     |     |          |           |           |           | 
# |     +---- | --> u    7           5           7     8     5 
# |           |          |           |           |           | 
# |           |          |           |           |           | 
# 0-----------1          0-----4-----1           0-----4-----1 

# Tetrahedron:                          Tetrahedron10:

#                    v
#                  .
#                ,/
#               /
#            2                                     2                              
#          ,/|`\                                 ,/|`\                          
#        ,/  |  `\                             ,/  |  `\       
#      ,/    '.   `\                         ,6    '.   `5     
#    ,/       |     `\                     ,/       8     `\   
#  ,/         |       `\                 ,/         |       `\ 
# 0-----------'.--------1 --> u         0--------4--'.--------1
#  `\.         |      ,/                 `\.         |      ,/ 
#     `\.      |    ,/                      `\.      |    ,9   
#        `\.   '. ,/                           `7.   '. ,/     
#           `\. |/                                `\. |/       
#              `3                                    `3        
#                 `\.
#                    ` w
# Hexahedron:             Hexahedron20:          Hexahedron27:

#        v
# 3----------2            3----13----2           3----13----2     
# |\     ^   |\           |\         |\          |\         |\    
# | \    |   | \          | 15       | 14        |15    24  | 14  
# |  \   |   |  \         9  \       11 \        9  \ 20    11 \  
# |   7------+---6        |   7----19+---6       |   7----19+---6 
# |   |  +-- |-- | -> u   |   |      |   |       |22 |  26  | 23| 
# 0---+---\--1   |        0---+-8----1   |       0---+-8----1   | 
#  \  |    \  \  |         \  17      \  18       \ 17    25 \  18
#   \ |     \  \ |         10 |        12|        10 |  21    12| 
#    \|      w  \|           \|         \|          \|         \| 
#     4----------5            4----16----5           4----16----5 

# Prism:                      Prism15:               Prism18:

#            w
#            ^
#            |
#            3                       3                      3        
#          ,/|`\                   ,/|`\                  ,/|`\      
#        ,/  |  `\               12  |  13              12  |  13    
#      ,/    |    `\           ,/    |    `\          ,/    |    `\  
#     4------+------5         4------14-----5        4------14-----5 
#     |      |      |         |      8      |        |      8      | 
#     |    ,/|`\    |         |      |      |        |    ,/|`\    | 
#     |  ,/  |  `\  |         |      |      |        |  15  |  16  | 
#     |,/    |    `\|         |      |      |        |,/    |    `\| 
#    ,|      |      |\        10     |      11       10-----17-----11
#  ,/ |      0      | `\      |      0      |        |      0      | 
# u   |    ,/ `\    |    v    |    ,/ `\    |        |    ,/ `\    | 
#     |  ,/     `\  |         |  ,6     `7  |        |  ,6     `7  | 
#     |,/         `\|         |,/         `\|        |,/         `\| 
#     1-------------2         1------9------2        1------9------2 

# Pyramid:                     Pyramid13:                   Pyramid14:

#                4                            4                            4
#              ,/|\                         ,/|\                         ,/|\
#            ,/ .'|\                      ,/ .'|\                      ,/ .'|\
#          ,/   | | \                   ,/   | | \                   ,/   | | \
#        ,/    .' | `.                ,/    .' | `.                ,/    .' | `.
#      ,/      |  '.  \             ,7      |  12  \             ,7      |  12  \
#    ,/       .' w |   \          ,/       .'   |   \          ,/       .'   |   \
#  ,/         |  ^ |    \       ,/         9    |    11      ,/         9    |    11
# 0----------.'--|-3    `.     0--------6-.'----3    `.     0--------6-.'----3    `.
#  `\        |   |  `\    \      `\        |      `\    \     `\        |      `\    \
#    `\     .'   +----`\ - \ -> v  `5     .'        10   \      `5     .' 13     10   \
#      `\   |    `\     `\  \        `\   |           `\  \       `\   |           `\  \ 
#        `\.'      `\     `\`          `\.'             `\`         `\.'             `\` 
#           1----------------2            1--------8-------2           1--------8-------2
#                     `\
#                        u

# element_strings = {

# "brick27string" : """
# add element # {0} type 27NodeBrickLT 
#     with nodes ({1}, {2}, {3}, 
#                 {4}, {5}, {6}, 
#                 {7}, {8}, {9}, 
#                 {10}, {11}, {12}, 
#                 {13}, {14}, {15}, 
#                 {16}, {17}, {18}, 
#                 {19}, {20}, {21}, 
#                 {22}, {23}, {24}, 
#                 {25}, {26}, {27}) 
#     use material # {28} ;
# """,

# "brick8string" : """
# add element # {0} type 8NodeBrickLT 
#     with nodes ({1}, {2}, {3}, 
#                 {4}, {5}, {6}, 
#                 {7}, {8}) 
#     use material # {9} ;
# """,

# "shell4node" : """
# add element # {tag} type 4NodeShell_ANDES with nodes ({n1}, {n2}, {n3}, {n4}) use material # {p1}
#     thickness =  {p2};
# """
# }
