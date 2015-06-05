gmshtranslator
==============

### Table of contents

[toc]

###Introduction

Parse [gmsh](geuz.org/gmsh) `.msh` files and execute python code accordingly. Most useful to 
translate `.msh` files into other file formats or into input for simulation software.

###Requirements

`gmshtranslator` uses scipy. Obtain [here](http://www.scipy.org/).

###Installation

Run
	
	python setup.py install

###Usage

`gmshtranslator` works by parsing a gmsh mesh in the `.msh` format. Initialize by calling

	from gmshtranslator import gmshtranslator
	gt = gmshtranslator.gmshTranslator("filename.msh")  #Initialize the gmshtranslator object, and call it `gt`.

In a nutshell, `gmshtranslator` reads lines from a `.msh` file, matches these lines to user defined
`condition` (example condition: node belongs to a given physical group, or element of a certain type) and
executes a user defined action for the matching condition. A condition/action pair is called
a *rule*. Rules are classified into nodal rules and element rules, depending on what portion of
the `.msh` file they're working on. 

Conditions and actions are python functions (user defined) which have a given call signature. It
is by defining these rules that the user implements translation of `.msh` files into some other 
format. Nodal rules match patterns between the `$Nodes` and `$EndNodes` tags withing the `.msh` file, and execute actions accordingly. Element rules do the same between the `$Elements` and 
`$EndElements` tags. Contents of each line are passed into rules and actions functions and the
user implements what to do with them. More on this later.

Upon initializing, `gmshtranslator` does an initial pass on the .msh file to recover some initial
useful information. The following member variables are available after initialization (`gt` is the parser object)

* `gt.Nnodes`: (Integer) Number of nodes in the mesh.
* `gt.Nelem`: (Integer) Number of elements in the mesh (total includes lines, surfaces and volume). Will typically be larger than the actual number of elements that will be used in an actual model.
* `gt.physical_groups`: (Python list of integers) List of tags (integer identification numbers) of available physical groups defined in the file.
* `gt.nodes_in_physical_groups`: (Python dictionary) Maps physical group number (tag, id) to nodes
belonging to that group. In gmsh only elements are associated with physical tags, so the meaning
of these nodes is that they connect to elements belonging to the given physical group. Therefore, as opposed to elements, nodes can belong to more than one physical group. 

Once the file is initially read, the user can use the above information to do some initial memory 
pre-allocation according to his or her needs. Then, the user implements rules for nodes and elements and informs `gmshtranslator` of these rules. Finally, the `gt.parse()` function is called
and the file is parsed using the user defined rules. 


#### Nodal rule functions syntax:

A nodal rule is composed of a condition and an action functions. A condition function has
the following syntax:

		nodal_condition_name(tag,x,y,z,physgroups)

`gmshtranslator` calls the condition and with the arguments given above, and the function
should evaluate to `True` or `False`. `tag` will be an integer with the node id; `x`, `y`, and `z`
will be double-precision numbers with the nodal coordinates, finally `physgroups` is a list
with the physical group tags the node belongs to. An example nodal condition is given below:

		def node_in_unit_box(tag,x,y,z,physgroups):
			return (1.0 <= x) and ( x <= 1.0) and (1.0 <= y) and ( y <= 1.0) and (1.0 <= z) and ( z <= 1.0) 

which returns `True` if the node is within the unit box. Combining the different input arguments, the user can provide much functionality in the the kind of conditions that are met. Additionally,
using global variables, values can be stored for later use. 

Nodal actions are functions which return no value, and are executed if the condition associated with it (within the same rule) returns true. The syntax is:

		nodal_action_name(tag,x,y,z)

As before, the nodal action receives the node tag and its coordinates. Arbitrary python code
can be executed at this point. The following example implementation prints out the tag and the coordinates.

		def print_node_info(tag, x,y,z):
			print "Node # {} is located at ({},{},{})".format(tag,x,y,z)


#### Element rule functions syntax:

Element rules are analogous to nodal rules, with varying syntax, and must evaluate to a boolean
thruth value. The syntax is:

		element_condition_name(eletag,eletype,physgrp,nodes)

Here, `eletag` is the (gmsh) element tag, `eletype` is an integer which describes the type of element 
associated with the line (line, brick, etc.), `physgrp` is an integer tag indicating the
physical group that the element belongs to, and `nodes` is an integer list with the tags of the
nodes which define the elements. (**Warning FEA users!!** the numbering of the nodes *might* not 
match your application). `gmshtranslator` defines some constants that can be used to simplify 
the matching of `eletype` to specific elements. For example, `gt.hexahedron_8_node` gives the
integer tag cooresponding to an 8-node hexahedron element (5). More tags are available at the end of this 
readme. As an example, the following element condition evaluates to true for 8-node bricks:

		def is_hexahedron(eletag,eletype,physgrp,nodes):
			return eletype==gt.hexahedron_8_node

Element actions are similar to nodal actions. The syntax is as follows:

		element_action_name(eletag,eletype,physgrp,nodes)

Where `eletag` is the integer element tag, `eletype` is the element type as described before, 
`physgrp` is the integer physical group tag, and `nodes` is a list of integers specifying the
nodes belonging to the element.

The following action prints a message for hexahedrons:

		def print_brick_info(eletag,eletype,physgrp,nodes):
			print "Hexahedron with tag # {} connects the nodes: {},{},{},{},{},{},{},{}".format(eletag, nodes[0], nodes[1], nodes[2], nodes[3], nodes[4], nodes[5], nodes[6], nodes[7])


#### Informing `gmshtranslator` of node and element rules.

To inform `gmshtranslator` of a given nodal rule call the `add_nodes_rule(condition,action)` function 
with the names of the user defined condition and action functions. Conditions and actions can be reused
between different rules. All of the matching rules are executed (rules are not automatically mutually exclusive).

For example, to add the above nodal rule do:

	gt.add_nodes_rule(node_in_unit_box, print_node_info)

This will create a rule that will print the nodal info for all nodes within the unit box. 

For elements, the function is  `add_elements_rule(condition,action)`. As before the actions and conditions
can be reused, and all matching rules will be executed. Nodal conditions and rules cannot be mixed with
element conditions and rules (it makes no sense, and the calling signatures are different).

For example:

	gt.add_elements_rule(is_hexahedron, print_brick_info)

will add a rule that will print element info if it is a hexahedron. `.msh` files usually will have
more elements that would be used or mapped directly into an FE mesh. 

#### Example script

The following script reads `mymodel.msh` and parses it. It will print out the nodal coordinates of
the nodes in the unit box and the element info only if it is an hexahedron:

	from gmshtranslator import gmshtranslator
	gt = gmshtranslator.gmshTranslator("filename.msh")

	#Node rules
	def node_in_unit_box(tag,x,y,z,physgroups):
			return (1.0 <= x) and ( x <= 1.0) and (1.0 <= y) and ( y <= 1.0) and (1.0 <= z) and ( z <= 1.0) 
	def print_node_info(tag, x,y,z):
			print "Node # {} is located at ({},{},{})".format(tag,x,y,z)
	gt.add_nodes_rule(node_in_unit_box, print_node_info)


	#Element rules
	def is_hexahedron(eletag,eletype,physgrp,nodes):
			return eletype==gt.hexahedron_8_node
	def print_brick_info(eletag,eletype,physgrp,nodes):
			print "Hexahedron with tag # {} connects the nodes: {},{},{},{},{},{},{},{}".format(eletag, nodes[0], nodes[1], nodes[2], nodes[3], nodes[4], nodes[5], nodes[6], nodes[7])
	gt.add_elements_rule(is_hexahedron, print_brick_info)


	#Execute
	gt.parse()


### Tricks with global variables. 

`gmshtranlator` only stores the information detailed in the usage section (number of nodes, elements and physical group info). 
Sometimes one needs to store some information and pass that information between the rules for more complex
mesh processing. For example, if you only want to print the brick info for the bricks that have a node
that belongs to the unit box (rather boringly assuming you don't have a phyical group set up for the unit box ) 
one can pass the necesary extra information to the condition using global variables. 

The following script will do just that:


	from gmshtranslator import gmshtranslator
	gt = gmshtranslator.gmshTranslator("filename.msh")

	nodes_in_unit_box = []  #A list to hold the node tags

	#Node rules
	def node_in_unit_box(tag,x,y,z,physgroups):
			return (1.0 <= x) and ( x <= 1.0) and (1.0 <= y) and ( y <= 1.0) and (1.0 <= z) and ( z <= 1.0) 
	def print_node_info(tag, x,y,z):
			global nodes_in_unit_box
			nodes_in_unit_box.append(tag)
			print "Node # {} is located at ({},{},{})".format(tag,x,y,z)
	gt.add_nodes_rule(node_in_unit_box, print_node_info)


	#Element rules
	def is_hexahedron_in_the_unit_box(eletag,eletype,physgrp,nodes):
			global nodes_in_unit_box
			is_in_unit_box = False
			for node in nodes:
				if node in nodes_in_unit_box:
					is_in_unit_box = True
					break
			#Will evaluate to true if element is a hexa and is in the unit box.
			return eletype==gt.hexahedron_8_node and is_in_unit_box 
	def print_brick_info(eletag,eletype,physgrp,nodes):
			print "Hexahedron with tag # {} connects the nodes: {},{},{},{},{},{},{},{}".format(eletag, nodes[0], nodes[1], nodes[2], nodes[3], nodes[4], nodes[5], nodes[6], nodes[7])
	gt.add_elements_rule(is_hexahedron, print_brick_info)


	#Execute
	gt.parse()

**Avoid pitfall!!** The variable `nodes_in_unit_box` will only be filled when `gt.parse()` is called, and
after the corresponding rule is matched. Therefore, looping over the list will only make sense after
`gt.parse` is called.


### Available element types:

As of gmsh 2.9.3 the integer element types are mapped as follows:

* `line_2_node` (1): 2-node line.
* `triangle_3_node` (2): 3-node triangle.
* `quadrangle_4_node` (3): 4-node quadrangle.
* `tetrahedron_4_node` (4): 4-node tetrahedron.
* `hexahedron_8_node` (5): 8-node hexahedron.
* `prism_6_node` (6): 6-node prism.
* `pyramid_5_node` (7): 5-node pyramid.
* `line_3_node` (8): 3-node second order line (2 nodes associated with the vertices and 1 with the edge).
* `triangle_6_node` (9): 6-node second order triangle (3 nodes associated with the vertices and 3 with the edges).
* `quadrangle_9_node` (10): 9-node second order quadrangle (4 nodes associated with the vertices, 4 with the edges and 1 with the face).
* `tetrahedron_10_node` (11): 10-node second order tetrahedron (4 nodes associated with the vertices and 6 with the edges).
* `hexahedron_27_node` (12): 27-node second order hexahedron (8 nodes associated with the vertices, 12 with the edges, 6 with the faces and 1 with the volume).
* `prism_18_node` (13): 18-node second order prism (6 nodes associated with the vertices, 9 with the edges and 3 with the quadrangular faces).
* `pyramid_14_node` (14): 14-node second order pyramid (5 nodes associated with the vertices, 8 with the edges and 1 with the quadrangular face).
* `point_1_node` (15): 1-node point.
* `quadrangle_8_node` (16): 8-node second order quadrangle (4 nodes associated with the vertices and 4 with the edges).
* `hexahedron_20_node` (17): 20-node second order hexahedron (8 nodes associated with the vertices and 12 with the edges).
* `prism_15_node` (18): 15-node second order prism (6 nodes associated with the vertices and 9 with the edges).
* `pyramid_13_node` (19): 13-node second order pyramid (5 nodes associated with the vertices and 8 with the edges).
* `triangle_9_node_incomplete` (20): 9-node third order incomplete triangle (3 nodes associated with the vertices, 6 with the edges)
* `triangle_10_node` (21): 10-node third order triangle (3 nodes associated with the vertices, 6 with the edges, 1 with the face)
* `triangle_12_node_incomplete` (22): 12-node fourth order incomplete triangle (3 nodes associated with the vertices, 9 with the edges)
* `triangle_15_node` (23): 15-node fourth order triangle (3 nodes associated with the vertices, 9 with the edges, 3 with the face)
* `triangle_15_node_incomplete` (24): 15-node fifth order incomplete triangle (3 nodes associated with the vertices, 12 with the edges)
* `triangle_21_node` (25): 21-node fifth order complete triangle (3 nodes associated with the vertices, 12 with the edges, 6 with the face)
* `edge_4_node` (26): 4-node third order edge (2 nodes associated with the vertices, 2 internal to the edge)
* `edge_5_node` (27): 5-node fourth order edge (2 nodes associated with the vertices, 3 internal to the edge)
* `edge_6_node` (28): 6-node fifth order edge (2 nodes associated with the vertices, 4 internal to the edge)
* `tetrahedron_20_node` (29): 20-node third order tetrahedron (4 nodes associated with the vertices, 12 with the edges, 4 with the faces)
* `tetrahedron_35_node` (30): 35-node fourth order tetrahedron (4 nodes associated with the vertices, 18 with the edges, 12 with the faces, 1 in the volume)
* `tetrahedron_56_node` (31): 56-node fifth order tetrahedron (4 nodes associated with the vertices, 24 with the edges, 24 with the faces, 4 in the volume)
* `hexahedron_64_node` (92): 64-node third order hexahedron (8 nodes associated with the vertices, 24 with the edges, 24 with the faces, 8 in the volume)
* `hexahedron_125_node` (93): 125-node fourth order hexahedron (8 nodes associated with the vertices, 36 with the edges, 54 with the faces, 27 in the volume).

Use any of these member values for parsing. For example, if `gt` is the name of the parser object, then
`gt.prism_15_node` evaluates to the integer number 18.