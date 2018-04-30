from graphlib import GraphDB, Graph, NEATO, print_stats
import sys

db = GraphDB(sys.argv[1])

def gen_to2():
	gphs = []
	working = [Graph.full(7)]
	while working:
		g = working.pop()
		for child in g.symmetry():
			if child and child not in gphs:
				gphs.append(child)
				working.append(child)
	return gphs
		

def gen_to():
	gphs = [set([Graph()]), set(), set(), set(), set(), set(), set()]

	for gi in range(len(gphs)-1):
		for g in gphs[gi]:
			for c in range(len(g)):
				gphs[gi+1].update(list(g.gen_children(c+1)))
	return  gphs

g = Graph.full(6)
print(g.str())
g.symmetry(db)
g.identify(db)
print(g.str())

db.gen()
#~ NEATO(db.each_graph(), 'deep.png', force_sym=False)

def make_subs():
	subs = set()
	for g in db.each_graph():
		print(g)
		g.symmetry()
		for sub in g.sym_nodes:
			test = set()
			for seed in sub:
				test.add( g.subgraph(sub, seed))
			assert(len(test) == 1)
			subs.update(test)#g.symmetrical_subgraphs(g.sym))

	NEATO(subs, "subs.png", "circo")


def single_sym():
	single = set()
	for g in db.each_graph():
		print(g)
		g.symmetry()
		if len(g.sym_nodes) == 1:
			single.add(g)
	NEATO(single, "singe_node_sym.png", "circo")


#~ gphs  = list(db.each_graph("nedges=10"))
#~ print("%d graphs"%len(gphs))
#~ NEATO(gphs, "aritym3.png")

#~ g1 = Graph().add_node([0]).add_node([0, 1]).add_node([2]).add_node([3]).add_node([3,4])
#~ g2 = Graph.ring(6).add_edge(0,3)

#~ NEATO([g1, g2],'gregor.png')
#~ g1.fingerprint()
#~ g2.fingerprint()

#~ db.lookup(Graph())

#~ db.gen2(7)

#~ db.lookup(Graph.full(7))
#~ g2 = db.lookup(g)
#~ print(g)
#~ print(g2)


#~ g = db.get_parentless_graph()
#~ while g:
	#~ g.symmetry(db)
	#~ db.set_flag(g, GraphDB.F_HAS_EPARENTS)
	#~ g = db.get_parentless_graph()
	
#~ print(g.str())

#~ g.symmetry(db)
#~ db.set_flag(g, GraphDB.F_HAS_EPARENTS)

#~ NEATO(db.each_graph(), "test.png")
#~ for g in db.each_graph():
	#~ print(g)

#~ g = Graph().add_node([0]).add_node([0,1]).add_node([0])
#~ print(g)

#~ g.calc_symmetry()
#~ print(NEATO([g], "g.png"))

#~ gphs = gen_to()
#~ gphs = gen_to2()

#~ print("LEN: %d"%len(gphs))
#~ NEATO(gphs, "ALL.png")

#~ print(gphs[5])
#~ for i in range(0, len(gphs)):
	#~ print("%d: %d gphs"%(i+1, len(gphs[i])))
	#~ NEATO(gphs[i], "g%d.png"%(i+1))

#~ N_HARD_EQ 44072049
#~ N_CALC    11420
#~ N_EQ      23820
#~ N_HASH_EQ 2786546

#~ N_HARD_EQ 46309337
#~ N_CALC    19235
#~ N_EQ      25442
#~ N_HASH_EQ 33257
#~ N_HARD_EQ 52200657
#~ N_CALC    22839
#~ N_EQ      30150
#~ N_HASH_EQ 56667

#~ NEATO(db.each_graph(), "full.png")
#~ from graphlib import N_HARD_EQ, N_EQ, N_CALC, N_HASH_EQ
#~ print("N_HARD_EQ %d"%N_HARD_EQ)
#~ print("N_CALC    %d"%N_CALC)
#~ print("N_EQ      %d"%N_EQ)
#~ print("N_HASH_EQ %d"%N_HASH_EQ)

#~ gA, gB = g.rem_edge(0, 3)
#~ print(gA)
#~ print(gB)

#~ NEATO([g, gA, gB], 'break.png')

	
#~ for i in range(len(gphs)):
	#~ NEATO(gphs[i], 'graphs_%d.png'%(i+1))

#~ for g in gphs[5]:
	#~ col = list(filter(lambda x: hash(x) == hash(g), gphs[5]))
	#~ if len(col) > 1:
		#~ NEATO(col, "%x.png"%hash(g))
	

#~ print(len(gphs[5]))
#~ graphs = [Graph()]	

#~ i =0
#~ while len(graphs) < 4:
	#~ for z in graphs[i].generate_children(1):
		#~ graphs.append(z)
	#~ i+=1
	
#~ for g in graphs:
	#~ print(g.adj, g.recalc().hash)


print(db.count())
print_stats()
db.close()
