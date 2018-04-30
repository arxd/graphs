requirejs(['util'], function ($) {

function Node(id, xy=[0,0])
{
	this.color = 'black';
	this.id = id;
	//~ this.sym = -1;
	this.pos = xy;
	this.hover = false;
	this.selected = false;
	this.edges = [];
}

Node.prototype.remove_edge = function(edge)
{
	var i=0;
	while(!this.edges[i].eq(edge))
		i++;
	this.edges.splice(i,1);
}

Node.prototype.render = function(ctx)
{
	if (this.hover) {
		ctx.fillStyle = "#888";
		ctx.beginPath();
		ctx.arc(this.pos[0], this.pos[1],2, 0, 2 * Math.PI);
		ctx.fill();
	}
	if (this.selected) {
		ctx.strokeStyle = "red";
		ctx.lineWidth=0.2;
		ctx.beginPath();
		ctx.arc(this.pos[0], this.pos[1],2, 0, 2 * Math.PI);
		ctx.stroke();
	}
	
	ctx.fillStyle = this.color;
	ctx.beginPath();
	ctx.arc(this.pos[0], this.pos[1],1, 0, 2 * Math.PI);
	ctx.fill();


}

Node.prototype.dist = function(xy)
{
	const dx = xy[0]-this.pos[0];
	const dy = xy[1]-this.pos[1];
	return Math.sqrt(dx*dx+dy*dy);
}

function Edge(nA, nB)
{
	this.id = 0;
	this.color = 'black';
	this.nA = nA;
	this.nB = nB;
}

Edge.prototype.render = function(ctx)
{
	ctx.lineWidth = 0.7;
	ctx.strokeStyle = this.color;
	ctx.beginPath();
	ctx.moveTo(this.nA.pos[0], this.nA.pos[1]);
	ctx.lineTo(this.nB.pos[0], this.nB.pos[1]);
	ctx.stroke();
}

Edge.prototype.eq = function(other)
{
	if (this.nA == other.nA && this.nB == other.nB)
		return true;
	if (this.nA == other.nB && this.nB == other.nA)
		return true;
	return false;
}

Edge.prototype.other = function(n)
{
	if (n === this.nA)
		return this.nB;
	if (n === this.nB)
		return this.nA;
	return undefined;
}

function Graph()
{
	this.el = $.DIV(); // a dummy element for events
	this.nodes = [new Node(0)];
	this.edges = [];
}

Graph.prototype.add_edge = function(edge)
{
	if (typeof edge.nA == 'number') {
		if (edge.nA < 0 || edge.nA >= this.nodes.length || edge.nB <0 || edge.nB >=this.nodes.length)
			console.error("Edge node out of range");
		edge.nA = this.nodes[edge.nA];
		edge.nB = this.nodes[edge.nB];
	}
	for (var e = 0; e < this.edges.length; e++) {
		if (this.edges[e].eq(edge))
			return false;
	}
	edge.id = this.edges.length;
	this.edges.push(edge);
	edge.nA.edges.push(edge);
	edge.nB.edges.push(edge);
	return true;
}

Graph.prototype.remove_edge = function(edge)
{
	for (var i=0; i < this.edges.length; ++i) {
		if (this.edges[i].eq(edge))
			break;
	}
	if (i < this.edges.length) {
		this.edges[i].nA.remove_edge(this.edges[i]);
		this.edges[i].nB.remove_edge(this.edges[i]);
		this.edges.splice(i, 1);
	}
}

Graph.prototype.remove_node = function (node)
{
	for (var i = this.edges.length-1; i >=0; i--) {
		if (this.edges[i].nA == node || this.edges[i].nB == node) {
			this.edges[i].nA.remove_edge(this.edges[i]);
			this.edges[i].nB.remove_edge(this.edges[i]);
			this.edges.splice(i, 1);
		}
	}
	var i=0;
	while (this.nodes[i] != node)
		i++;
	this.nodes.splice(i, 1);
}

Graph.prototype.toString = function()
{
	var s = 'n:'+this.nodes.length + ", e:"+0+'\n';
	for (var n in this.each_node) {
		s += '    '+n.id+'\n';
	}
	return s;
}

Graph.prototype.each_node = function*()
{
	for(var i=0; i < this.nodes.length; ++i)
		yield this.nodes[i];
}
Graph.prototype.each_edge = function*()
{
	for(var i=0; i < this.edges.length; ++i)
		yield this.edges[i];
}

Graph.prototype.render = function(ctx)
{
	for (var e of this.each_edge())
		e.render(ctx);
	for (var n of this.each_node())
		n.render(ctx);
}

Graph.prototype.identify = function()
{
	for (var n of this.each_node())
		n.id = -1;

	var graphs = [];
	for (var ni=0; ni < this.nodes.length; ++ni ) {
		if (this.nodes[ni].id >= 0)
			continue;
		var nodes = [this.nodes[ni]];
		nodes[0].id = 0;
		var visit = [this.nodes[ni]];
		while (visit.length) {
			var n = visit.pop();
			for (var e =0; e < n.edges.length; ++e) {
				var other = n.edges[e].other(n);
				if (other.id < 0) {
					other.id = nodes.length;
					nodes.push(other);
					visit.push(other);
				}
			}
		}
		var gph = [];
		for (var n=0; n < nodes.length; ++n) {
			var adj = [];
			for (var e =0; e < nodes[n].edges.length; e++)
				adj.push(nodes[n].edges[e].other(nodes[n]).id);
			gph.push(adj);
		}
		graphs.push({nodes:nodes, adj:gph});
	}
	return graphs;
}

Graph.prototype.lookup = function()
{
	var colors = ["#000000", "#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00", "#ffff33", "#a65628", "#f781bf",
	"#66c2a5", "#fc8d62", "#8da0cb", "#e78ac3", "#a6d854", "#ffd92f", "#e5c494", "#b3b3b3"];
	var graphs = this.identify();
	var adj = [];
	for (var g in graphs)
		adj.push(graphs[g].adj);
	window.socket.send_recv(this, 'lookup', [adj], function(resp) {
		if (resp.length != graphs.length)
			console.error("Lengths don't match!");
		for (var g=0; g < graphs.length; g++) {
			var gph = graphs[g].nodes;
			for (var n=0; n < gph.length; n++) {
				gph[n].color = colors[resp[g].nsym[n]+2];
				for (var e=0; e < gph[n].edges.length; ++e) {
					var sym = resp[g].esym[gph[n].edges[e].nA.id+'-'+gph[n].edges[e].nB.id];
					if (sym == undefined)
						sym = resp[g].esym[gph[n].edges[e].nB.id+'-'+gph[n].edges[e].nA.id];
					gph[n].edges[e].color = colors[sym+1];
				}
			}
		}
		this.el.dispatchEvent(new Event("changed"));
	});
	
}

SELECT = 1
GRAB = 2
ROTATE = 3
MIRROR = 4
EDGE_DRAW = 5

function Editor()
{
	this.el = $.EL('canvas', 'Editor');
	this.g = new Graph();
	this.ctx = this.el.getContext("2d");
	this.resize();
	this.running = false;
	this.state = SELECT;
	this.cur_hover = null;
	this.cur_xy = [0,0];
	
	$.THROTTLE(this, window, 'resize', 100, function() {this.resize();});
	$.THROTTLE(this, window, 'mousemove', 100, function(e) {
		var scale = 64/this.el.height;
		var x = scale*(e.clientX-this.el.width/2);
		var y = scale*(e.clientY-this.el.height/2);
		this.cur_xy = [x,y];
		if (this.state == GRAB) {
			this.mid_grab();
		} else if (this.state == EDGE_DRAW) {
			this.update_hover();
			this.mid_edge_draw();
		} else {
			this.update_hover();
		}
	});
	$.LISTEN(this, window, 'keydown', function(e) {
		if (this.state == SELECT) {
			switch(e.key) {
				case 'x':this.delete_selected(); break;
				case 'n':this.drop_node(this.cur_xy); break;
				case ' ': this.toggle_select(this.cur_hover); break;
				case 'a': this.toggle_all();break;
				case 'c': this.connect_selected(); break;
				case 'g': this.start_grab(); break;
				default:		console.log(e.key);break;
			}
		} else if (this.state == GRAB) {
			switch (e.key) {
				case 'g': this.end_grab(); break;
			}
		}
			
	});
	
	$.LISTEN(this, window, 'mousedown', function(e) {
		if (this.state == SELECT) {
			if (e.button == 1) {
				this.start_edge_draw();
			} else if (e.button == 0) {
				this.start_single_grab();
			}
		} else if (this.state == GRAB) {
			this.end_grab();
		}
	});
	
	$.LISTEN(this, window, 'mouseup', function(e) {
		if (this.state == EDGE_DRAW) {
			this.end_edge_draw();
			this.state = SELECT;
		} else if (this.state == GRAB) {
			this.end_grab();
			this.state = SELECT;
		}
	});
	
	$.LISTEN(this, this.g.el, 'changed', function(e) {
		this.render();
	});
}

Editor.prototype.delete_selected = function()
{
	for (var n of this.g.each_node())
		if (n.selected)
			this.g.remove_node(n);
	this.g.lookup();
	this.render();
}

Editor.prototype.start_single_grab = function()
{
	for (var n of this.g.each_node())
		n.selected = (n === this.cur_hover);
	this.start_grab();
}

Editor.prototype.start_grab = function()
{
	this.start_xy = this.cur_xy;
	this.state = GRAB;
	for (var n of this.g.each_node()) {
		if (n.selected)
			n.old_pos = n.pos.slice();
	}
	this.render_loop();
}

Editor.prototype.mid_grab = function()
{
	for (var n of this.g.each_node()) {
		if (n.selected) {
			n.pos[0] = n.old_pos[0] + (this.cur_xy[0] - this.start_xy[0]);
			n.pos[1] = n.old_pos[1] + (this.cur_xy[1] - this.start_xy[1]);
		}
	}
}

Editor.prototype.end_grab = function()
{
	for (var n of this.g.each_node()) {
		n.old_pos = undefined;
	}
	this.render_stop();
	this.state = SELECT;
}

Editor.prototype.start_edge_draw = function()
{
	this.start_node = this.cur_hover;
	this.prev_node = this.cur_hover;
	this.state = EDGE_DRAW;
}

Editor.prototype.mid_edge_draw = function()
{
	if (this.prev_node == this.cur_hover)
		return;
	const edge = new Edge(this.prev_node, this.cur_hover);
	if (!this.g.add_edge(edge))
		this.g.remove_edge(edge);
	this.prev_node = this.cur_hover;
	this.g.lookup();
	this.render();
}

Editor.prototype.end_edge_draw = function()
{
	if (this.start_node != this.cur_hover)
		return;
	for (var n of this.g.each_node()) {
		n.selected = (n === this.cur_hover);
	}
	this.render();
}


Editor.prototype.connect_selected = function()
{
	var edges = [];
	function add_edge(edge) {
		for (var i=0; i < edges.length; ++i) {
			if (edge.eq(edges[i]))
				return true;
		}
		edges.push(edge);
	}
	
	for (var n1 of this.g.each_node()) {
		if (!n1.selected)
			continue;
		for (var n2 of this.g.each_node()) {
			if (!n2.selected || n2 === n1)
				continue;
			add_edge(new Edge(n1,n2));
		}
	}
	
	var keep=false;
	for (var e=0; e < edges.length; ++e)
		keep |= this.g.add_edge(edges[e]);
	if (!keep)
		for (var e=0; e < edges.length; ++e)
			this.g.remove_edge(edges[e]);
	this.g.lookup();
	this.render();

}

Editor.prototype.toggle_all = function()
{
	var all_selected = true;
	for (var n of this.g.each_node()) {
		all_selected &= n.selected;
		n.selected = true;
	}
	if (all_selected) 
		for (var n of this.g.each_node())
			n.selected = false;
	this.render();
}

Editor.prototype.toggle_select = function(node)
{
	if (!node)
		return;
	node.selected = !node.selected;
	this.render();
}

Editor.prototype.drop_node = function(xy)
{
	this.g.nodes.push(new Node(this.g.nodes.length, xy));
	this.g.lookup();
	this.render();
}

Editor.prototype.update_hover = function()
{
	var min = {dist:1e10, n:0};
	
	for (var n of this.g.each_node()) {
		const d = n.dist(this.cur_xy);
		if (d < min.dist) {
			min.dist = d;
			min.n = n;
		}
	}
	if (min.n != this.cur_hover) {
		if (this.cur_hover)
			this.cur_hover.hover = false;
		this.cur_hover = min.n;
		this.cur_hover.hover = true;
		this.render();
	}
}


Editor.prototype.resize = function()
{
	const w = document.body.clientWidth;
	const h = document.body.clientHeight;
	//console.log("RESIZE "+w+"x"+h);
	
	this.el.height = h;
	this.el.width = w;
	this.aspect = w/h;
	this.ctx.translate(w/2, h/2);
	this.ctx.scale(h/64, h/64);
	this.render();
}

Editor.prototype.render_loop = function()
{
	this.running = true;
	this.render();
}

Editor.prototype.render_stop = function()
{
	this.running= false;
}

Editor.prototype.render = function()
{
	this.render_frame();
	if (this.running)
		requestAnimationFrame($.DO(this, this.render));
}

Editor.prototype.render_frame = function()
{
//~ 	ctx.fillStyle = "#"+(Math.floor(Math.random()*1000)+'000').slice(-2);
	this.ctx.fillStyle = '#ddd';
	this.ctx.rect( -1000, -1000, 2000, 2000,);
	this.ctx.fill();
	this.g.render(this.ctx);
	

}

document.body.append((new Editor()).el);
window.socket = new $.SOCKET('Connection');
window.socket.connect('/ctrl', function(e){
	//~ console.log("Fetching plays");
	//~ window.simple.fetch_plays((new Date()).getFullYear());
});
document.body.append(window.socket.el);

});
