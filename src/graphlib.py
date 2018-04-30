import sqlite3
import hashlib,struct,itertools,math

STATS = {'compare_nosym':0, 'hash_calc':0, 'perms':0, 'row_init':0, 'row_init_sym':0, 'graph_eq_graph':0, 'symmetry':0, 'symmetry_calc':0}
def print_stats():
	for k,v in STATS.items():
		print(" %16s : %d"%(k,v))

class SQLObj(object):
	def __init__(self, conn=None, row=None):
		self.conn = None
		self.id = None
		if conn:
			self.conn = conn
			self.init_from_row(row)
		else:
			self.init_default()

	def init_from_row(self, row):
		pass
		
	def update(self):
		assert(self.conn)


def hash_junk(junk):
	hash = 1
	for j in junk:
		hash ^= struct.unpack("L", hashlib.md5(j).digest()[:8])[0]
	return hash
	

def NEATO(graphs, filename=None, prog="fdp", force_sym=True):
	from subprocess import Popen, PIPE
	gstr = 'graph{\nnode [width=0.2, shape=point];\nedge [penwidth=4];\n'
	for gi, g in enumerate(graphs):
		if g:
			gstr += g.dot('N%d_'%gi, force_sym=force_sym)
	gstr +='\n}\n'
	if filename:
		dot = Popen([prog, '-Tpng', '-o'+filename], stdin=PIPE)
		dot.communicate(gstr)
	return gstr


class Graph(SQLObj):
	""" Graphs are immutable
	"""
	@staticmethod
	def full(size):
		assert(size >= 1)
		return Graph([set(filter(lambda n: n!= t, range(size))) for t in range(size)])
		
	@staticmethod
	def ring(size):
		assert(size >= 1)
		return Graph( [set([(t-1+size)%size, (t+1)%size]) for t in range(size)])
				
	def __init__(self, row=None, connect=[]):
		"""
			id:
			hash:
			edges:
			parents: ???
			node_sym:
			sym_nodes:
			edge_sym:
			max_edge_sym:
			"""
		self.id = 0
		self.hash = None
		self.edges = None
		self.parents = None
		self.node_sym = None
		self.edge_sym = None
		self.sym_nodes = None
		self.sym_edges = None
		
		if isinstance(row, Graph):
			self.adj = [s.copy() for s in row.adj]
			for a,b in connect:
				self._connect(a,b)
			self._calc()
		elif row == None:
			self.adj = [set()]
			for a,b in connect:
				self._connect(a,b)
			self._calc()
		elif isinstance(row, list): #adj list
			self.adj = [set(x) for x in row]
			self._calc()
		else:# db row
			global STATS
			STATS['row_init'] += 1
			self.id = row[0]
			self.hash = row[1]
			# add rows
			self.adj = [set() for s in range(row[2])]
			# row symmetry
			if row[3] != None:
				STATS['row_init_sym'] += 1
				self.node_sym = list(bytearray(row[3],'ascii'))
				assert(len(self.node_sym) == len(self.adj))
				self.sym_nodes = [set() for t in range(max(self.node_sym)+1)]
				for s in range(len(self.adj)):
					self.sym_nodes[self.node_sym[s]].add(s)
				
			# add edges 
			self.edges = set()
			edgbytes = bytearray(row[4],'ascii')
			for e in range(0, len(edgbytes), 2):
				nA = edgbytes[e]
				nB = edgbytes[e+1]
				self.adj[nA].add(nB)
				self.adj[nB].add(nA)
				self.edges.add((nA, nB))
			
			# edge symmetry
			if row[5]!=None:
				edge_sym_bytes = list(bytearray(row[5],'ascii'))
				self.edge_sym = {}
				self.sym_edges = [set() for t in range((max(edge_sym_bytes) if edge_sym_bytes else -1)+1)]
				for s in range(len(edge_sym_bytes)):
					e = (edgbytes[s*2], edgbytes[s*2+1])
					self.edge_sym[e] = edge_sym_bytes[s]
					self.sym_edges[edge_sym_bytes[s]].add(e)
			
			self._fingerprint()
			
			
	def _connect(self, nA, nB):
		if nA == len(self.adj) or nB == len(self.adj):
			self.adj.append(set())
		#~ new = nA not in self.adj[nB]
		self.adj[nA].add(nB)
		self.adj[nB].add(nA)

	def _fingerprint(self):
		self.node_fp = []
		self.fingerprints = {}
		for n in range(len(self.adj)):
			fp = tuple(sorted([len(self.adj[a]) for a in self.adj[n]]))
			self.node_fp.append(fp)
			try:
				self.fingerprints[fp].append(n)
			except:
				self.fingerprints[fp] = [n]
		

	def _calc(self):
		""" Called ONCE by the __init__ to calculate the hash and edges
		"""
		global STATS
		STATS['hash_calc'] += 1
		# calculate edges
		self.edges = set()
		for v, ve in enumerate(self.adj):
			for e in filter(lambda e: e>v, ve):
				self.edges.add((v,e))
		
		# Hash edges with arity
		hash_things = ["%dx%d"%(len(self.edges), len(self.adj))]
		self._fingerprint()
		for k,v in self.fingerprints.items():
			hash_things.append("%sx%d"%(k, len(v)))
			
			
		#~ aryedg = {}
		#~ for nA, nB in self.edges:
			#~ L,R = len(self.adj[nA]), len(self.adj[nB])
			#~ if R < L:
				#~ L, R = R, L
			#~ edg = (L<<8)+R
			#~ if edg in aryedg:
				#~ aryedg[edg] += 1
			#~ else:
				#~ aryedg[edg] = 1
		#~ for k, v in aryedg.iteritems():
			#~ hash_things.append("%dx%d"%(k, v))
	
		self.hash = hash_junk(hash_things)
		
		#~ if len(self.adj) == 1: # Special case: hardcode symmetry
			#~ self.node_sym = [0]
			#~ self.edge_sym = {}
			#~ self.sym_nodes = [set([0])]
			#~ self.sym_edges = []

		
	def identify(self, db):
		""" Update the current graph to match the data in the database \a db"""
		other = db.identify(self)
		self.id = other.id
		self.hash = other.hash
		self.adj = other.adj
		self.edges = other.edges
		self.node_sym = other.node_sym
		self.edge_sym = other.edge_sym
		self.sym_nodes = other.sym_nodes
		self.sym_edges = other.sym_edges
	
	def __hash__(self):
		return self.hash
	
	def __len__(self):
		return len(self.adj)

	def str(self, verbose=True):
		s = "v:%2d e:%2d, %x <%d>"%(len(self.adj), len(self.edges), self.hash&0xffffffffFFFFFFFF, self.id)
		if self.node_sym:
			s+= " %d/%d "%(len(self.sym_nodes), len(self.sym_edges))
		if verbose:
			s+='\n'
			for ni, n in enumerate(self.adj):
				s  += '  %d: %s'%(ni, list(n))
				if self.node_sym:
					s += '  (%d)'%self.node_sym[ni]
				s += '\n'
		return s

	def __str__(self):
		return self.str(False)
		

	def __eq__(self, other):
		assert(self.id and other.id)
		return self.id == other.id
		
		global STATS
		STATS['eq'] += 1
		
		if self.id and other.id:
			return self.id == other.id
		
		if hash(self) != hash(other):
			return False
			
		# Better find a mapping between nodes
		assert(self.node_sym and other.node_sym)
		
		nnodes = len(self.adj)
		assert(nnodes == len(other.adj))
		assert(len(self.edges) == len(other.edges))
		
		STATS['hard_eq'] += 1
		def eq(perm):
			STATS['permute'] += 1
			for ni in range(nnodes):
				if set(map(lambda e: perm[e], self.adj[ni])) != other.adj[perm[ni]]:
					return False
			return True
			
		for perm in itertools.permutations(range(nnodes)):
			if eq(perm):
				return  True
		return False
			
	
	def dot(self, prefix='N', force_sym=True):
		def clr(i):
			if i == 0:
				return "black"
			elif i <= 8:
				return "/set18/%d"%i
			elif i <= 16:
				return "/set28/%d"%(i-8)
			else:
				return "black"
		if force_sym: # Ensure we have symmetry data
			self.symmetry() 
		dot=""
		for ni in range(len(self.adj)):
			dot += '%s%d [color="%s"];\n'%(prefix, ni, clr(self.node_sym[ni]+2 if self.node_sym else 0))
		for nA, nB in self.edges:
			dot += '%s%d--%s%d [color="%s"];\n'%(prefix, nA, prefix, nB, clr(self.edge_sym[(nA,nB)]+1 if self.node_sym else 0))
		return dot
	
	#~ def subgraph(self, aset, seed):
		#~ """ Given a set of nodes \aset return a connected subgraph which has \a seed
		#~ as one of it's members
		#~ """
		#~ grph = Graph()
		
		#~ process_nodes = [seed]
		#~ mapping = [-1]*(max(aset)+1)
		#~ mapping[process_nodes[0]] = 0
		#~ while process_nodes:
			#~ node = process_nodes.pop()
			#~ for fn in filter(lambda x: x in aset, self.adj[node]):
				#~ if mapping[fn] < 0:
					#~ mapping[fn] = len(grph)
					#~ grph.adj.append(set())
					#~ process_nodes.append(fn)
				#~ grph._connect(mapping[node], mapping[fn])
		
		#~ return grph
		
	
	
	#~ def fingerprint(self):
		#~ def well_connected_groups(aset):
			#~ for n in aset:
				
		
		
		#~ fingerprints = [{'id':i, 'nodes':self.sym_nodes[i]} for i in range(len(self.sym_nodes))]
		
		
		#~ for fp in fingerprints:
			#~ fp['size'] = len(fp['nodes'])
			#~ fp['adj'] = set()
			#~ for n in fp['nodes']:
				#~ fp['adj'].update(self.adj[n])
		#~ print(fingerprints)
		

	#~ def add_edge(self, nA, nB):
		#~ assert(nA != nB)
		#~ assert(nA <= len(self.adj) and nA >= 0)
		#~ assert(nB <= len(self.adj) and nB >= 0)
		#~ adj2 = self.adj
		#~ return Graph(self, connect=[(nA,nB)])
		#~ gA._connect(nA, nB)
		#~ return gA
		
	def rem_edge(self, nA, nB):
		assert(nA != nB)
		assert(nA < len(self.adj) and nA >= 0)
		assert(nB < len(self.adj) and nB >= 0)
		
		mapping = [-1]*len(self.adj)
		def graph_from(start):
			mapping[start] = 0
			outstanding = [start]
			subg = [set()]
			while outstanding:
				node = outstanding.pop(0)
				for e in self.adj[node]:
					if (node == nA and e == nB) or (node == nB and e == nA):
						continue
					if mapping[e] < 0: # add a new node
						mapping[e] = len(subg)
						subg.append(set())
						outstanding.append(e)
					subg[mapping[node]].add(mapping[e])
			return Graph(subg)
		
		gA = graph_from(0)
		gB = None
		# search for another possible graph
		g2_start = 0
		while g2_start < len(mapping) and mapping[g2_start] >= 0:
			g2_start += 1
		if g2_start < len(mapping):
			gB = graph_from(g2_start)
		if gB and hash(gA) > hash(gB):
			return (gB, gA)
		return (gA, gB)
	
	def get_parents(self):
		if not self.parents:
			self.symmetry(force=True)
		return self.parents
		
	def symmetry(self, db, force=False):
		"""This function calculates 
			- parents:  A set of graphs, one for each edge removed.
			- edge_sym:  A mapping of (na,nb) edge tuples to sym id's
			- max_edge_sym:  The number of unique symmetry groups on edges
			- node_sym: An array indexed by the node id giving the node's symid
			- sym_nodes: The inverse of node_sym.  The index of the array is the symid.  Containing a set of nodes in that sym group.
		"""
		global STATS
		STATS['symmetry'] += 1
		if not self.id:  # Get our ID (and maybe our symmetry from the database)
			self.identify(db)
			
		if self.node_sym and not force:
			return
		STATS['symmetry_calc'] += 1
		
		self.parents = set()
		# First calculate edges
		mapping = {}
		#~ self.max_edge_sym = 0
		self.edge_sym = {}
		self.sym_edges = []
		for e in self.edges:
			gA, gB = self.rem_edge(*e)
			gA = db.identify(gA)
			gB = db.identify(gB)
			self.parents.add(gA)
			self.parents.add(gB)
			try:
				symid = mapping[(gA,gB)]
			except:
				symid = len(self.sym_edges)
				self.sym_edges.append(set())
				mapping[(gA,gB)] = symid
				
			self.edge_sym[e] = symid
			self.sym_edges[symid].add(e)
		
		#calculate node symmetry
		self.sym_nodes = []
		self.node_sym = []
		self.nodes = []
		mapping = {}
		for n, adj in enumerate(self.adj):
			s = tuple(sorted([self.edge_sym[(n, a) if n < a else (a, n)] for a in adj]))
			if s in mapping:
				self.sym_nodes[mapping[s]].add(n)#.append(mapping[s])
				self.node_sym.append(mapping[s])
			else:
				mapping[s] = len(self.sym_nodes)
				self.node_sym.append(len(self.sym_nodes))
				self.sym_nodes.append(set([n]))
		
		# Make sure our hard work is saved for next time
		db.save_symmetry(self)
		
		
	#~ def add_node(self, node_list):
		#~ node_list = set(node_list)
		#~ new = len(self.adj)
		#~ gph = Graph(self)
		#~ for s in node_list:
			#~ assert(s >= 0 and s < new)
			#~ gph.adj[s].add(new)
		#~ gph.adj.append(set(node_list))
		#~ return gph
	
	#~ def gen_children(self, nedges):
		#~ assert(nedges >= 1 and nedges <= len(self.adj))
		#~ for p in itertools.combinations(range(len(self.adj)), nedges):
			#~ yield self.add_node(p)

def graph_eq_graph(g1, g2, perm):
	global STATS
	STATS['graph_eq_graph'] += 1
	for ni in range(len(g1.adj)):
		if set(map(lambda e: perm[e], g1.adj[ni])) != g2.adj[perm[ni]]:
			return False
	return True
	
	

def graph_compare_nosym(g1, g2):
	global STATS
	perms = 1
	#~ print ("CMP %s:  %s"%(g1,g2))
	# First make sure the fingerprints match
	for k,v in g1.fingerprints.items():
		try:
			if len(g2.fingerprints[k]) != len(v):
				return False
		except:
			return False
		perms *= math.factorial(len(v))
	#if perms > 1000: #Threshold for amount of permutations we will try in this method
	#	return None
	STATS['perms'] += perms
	STATS['compare_nosym'] += 1
	
	# Create permutations of nodes given
	perm = [-1]*len(g1.adj)
	fingerprints = g1.fingerprints.keys()
	#~ print(fingerprints)
	def _gen_perms(fp):
		#~ print("!!!!"+str(fp))
		g1fp = g1.fingerprints[fingerprints[fp]]
		g2fp = g2.fingerprints[fingerprints[fp]]
		#~ print("%d: G2fp: "%fp+str(g2fp))
		for one_perm in itertools.permutations(g2fp):
			#~ print("    perm: "+str(one_perm))
			for p in range(len(one_perm)):
				perm[g1fp[p]] = one_perm[p]
				#~ print( "    > %d == %d"%(fp, len(fingerprints)-1))
				if fp == len(fingerprints)-1:
					#~ print("       -- "+str(perm))

					yield perm
				else:
					#~ print("       --AGAIN " + str(perm))
					for subp in _gen_perms(fp+1):
						yield subp
					#~ print("       --AFTER" + str(perm))
	
	for q in _gen_perms(0):
		#~ print(q)
		if graph_eq_graph(g1, g2, q):
			#~ print("Match")
			return True
	#~ print("Diff")
	return False
	
def graph_compare_sym(g1, g2):
	raise Exception("Oh no")

class GraphDB(object):
	
	F_HAS_ECHILDREN = 1
	F_HAS_EPARENTS = 2
	F_HAS_NCHILDREN = 4
	
	def __init__(self, filename):
		self.conn = sqlite3.connect(filename)
		self.create_nonexistant_tables()
		
	def create_nonexistant_tables(self):
		c = self.conn.cursor()

		# Create table
		c.execute('''CREATE TABLE IF NOT EXISTS Graphs (
			id INTEGER PRIMARY KEY,
			hash INTEGER NOT NULL, 
			nnodes INTEGER NOT NULL,  -- number of verticies
			nedges INTEGER NOT NULL,  -- number of edges
			edges BLOB NOT NULL,  -- [(b:vert,b:vert), ...]
			arity_max INTEGER NOT NULL, -- max num edges per node
			arity_avg INTEGER NOT NULL, 
			flags INTEGER NOT NULL, -- 1:Has children (One more edge)  2: Has Parents (One less edge)  4: Has node children (one more node
			
			--- Symmetry data ---
			node_sym BLOB, -- [symid, ...]  Symmetry info for each node
			n_node_sym INTEGER, -- Number of symids for nodes
			edge_sym BLOB, -- [symid, ...]  Symmetry info for each edge (index by ordering in edges)
			n_edge_sym INTEGER, -- Number of symids for edges
			
			internal_sym_id INTEGER -- An ID into the Symmetry table for a graph of the internal symmetry of this graph
		)''')
		c.execute('''CREATE TABLE IF NOT EXISTS Symmetry (
			id INTEGER PRIMARY KEY ,
			gid INTEGER NOT NULL , -- the shape of this data
			node_data BLOB NOT NULL -- [(b:loopback, b:arity), ...]
		)''')
		self.conn.commit()
	
	def set_flag(self, graph, flag):
		if not graph.id:
			graph = self.lookup(graph)
		#~ print("FLAG %s: %d"%(graph, flag))
		cur = self.conn.cursor()
		cur.execute("UPDATE Graphs SET flags = flags|? WHERE id = ?", (flag, graph.id))
		self.conn.commit()
		
	def count(self):
		cur = self.conn.cursor()
		cur.execute("SELECT nnodes, COUNT(nnodes) FROM Graphs GROUP BY nnodes")
		#~ cur.execute("SELECT nnodes, COUNT(nnodes) AS count, SUM(COUNT(nnodes)) OVER(count) AS total_count FROM Graphs GROUP BY nnodes")
		#~ cur.execute("SELECT nnodes, COUNT(1) as Cnt FROM Graphs GROUP BY nnodes UNION ALL SELECT 'SUM' nnodes, COUNT(1) FROM Graphs")
		count = [0]
		for row in cur.fetchall():
			if row[0] >= len(count):
				count += [0]*(row[0]-len(count)+1)
			count[row[0]] = row[1]
		return count


	def identify(self, graph):
		""" This only adds the graph if it is unique.
			It returns the graph that is in the database.
		"""
		if not graph:
			return None
		for g in self.each_graph("hash=?", (hash(graph), )):
			same = graph_compare_nosym(g, graph)
			if same == None:
				# Oh no.  We need symmetry to solve this problem
				graph.symmetry(self)
				g.symmetry(self)
				same = graph_compare_sym(g, graph)
			if same:
				return g
		
		# This graph was not found
		edge_buffer = bytearray()
		for nA, nB in graph.edges:
			edge_buffer.append(nA)
			edge_buffer.append(nB)
		arity_max = 0
		arity_avg = 0
		for n in graph.adj:
			arity = len(n)
			if arity > arity_max:
				arity_max = arity
			arity_avg += arity
		arity_avg /= float(len(graph))
		
		#~ print((hash(graph),
			#~ len(graph),
			#~ len(graph.edges),
			#~ edge_buffer,
			#~ arity_max,
			#~ arity_avg,
			#~ ))
		#~ print(type(edge_buffer))
		cur = self.conn.cursor()
		cur.execute("INSERT INTO Graphs (hash, nnodes, nedges, edges, arity_max, arity_avg, flags) VALUES (?,?,?,?,?,?,0)",
			(hash(graph),
			len(graph),
			len(graph.edges),
			bytes(edge_buffer),
			arity_max,
			arity_avg
			))
		graph.id = cur.lastrowid
		self.conn.commit()
		print("Add new graph: %s"%graph)
		return graph
	
	def save_symmetry(self, graph):
		cur = self.conn.cursor()
		cur.execute("UPDATE Graphs SET node_sym=?, n_node_sym=?, edge_sym=?, n_edge_sym=? WHERE id=?",
			(bytes(bytearray(graph.node_sym)), 
			len(graph.sym_nodes), 
			bytes(bytearray([graph.edge_sym[(nA,nB)] for nA, nB in graph.edges])	),
			len(graph.sym_edges),
			graph.id))
		self.conn.commit()
		
	def each_graph(self, where=None, args=()):
		cur = self.conn.cursor()
		cur.execute("SELECT id, hash, nnodes, node_sym, edges, edge_sym FROM Graphs%s"%("" if not where else " WHERE "+where), args)
		for row in cur.fetchall():
			yield Graph(row)
		
	def one_graph(self, where=None, args=()):
		cur = self.conn.cursor()
		cur.execute("SELECT id, hash, nnodes, node_sym, edges, edge_sym FROM Graphs%s"%("" if not where else " WHERE "+where), args)
		row = cur.fetchone()
		if row:
			return Graph(row)
		return None

	#~ def get_parentless_graph(self):
		#~ return 
	
	#~ def get_childless_graph(self):
		#~ cur = self.conn.cursor()
		#~ cur.execute("SELECT id, hash, nnodes, node_sym, edges, edge_sym) FROM Graphs WHERE flags&4 == 0 ORDER BY nnodes")
		#~ row = cur.fetchone()
		#~ if row:
			#~ return Graph(row)
		#~ return None

	def gen(self):
		g = self.one_graph("flags&2 == 0 ORDER BY nedges")
		while g:
			g.symmetry(self)
			self.set_flag(g, GraphDB.F_HAS_EPARENTS)
			g = self.one_graph("flags&2 == 0 ORDER BY nedges")

	#~ def gen2(self, max=100):
		#~ g = self.get_childless_graph()
		#~ while g and len(g) <= max:
			#~ for n in range(len(g)):
				#~ for g_child in g.gen_children(n+1):
					#~ self.lookup(g_child)
			#~ self.set_flag(g, GraphDB.F_HAS_NCHILDREN)
			#~ g = self.get_childless_graph()

		
		
	def close(self):
		self.conn.close()

