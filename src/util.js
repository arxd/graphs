
define([], function() {
	
//~ function DIST(p0, p1)
//~ {
	//~ var dx = p0[0] - p1[0];
	//~ var dy = p0[1] - p1[1];
	//~ return Math.sqrt(dx*dx+dy*dy);
//~ }
	
function Socket(cls)
{
	this.cls = cls;
	this.auto_connect = true;
	this.el = DIV(cls, "Conecting...");
	this.sock = null;
	LISTEN(this, window, 'unload');

}

Socket.prototype.connect = function(path, func=null)
{
	this.path = path;
	path = "ws://"+window.location.hostname+":"+window.location.port+path
	var sock = new WebSocket(path);
	LISTEN(this, sock, "open", function(){
		this.sock = sock;
		console.log("Socket open");
		this.el.innerHTML = "Connected";
		this.el.className = this.cls+' connected';
		
		if (func)
			func();
	});
	LISTEN(this, sock, "close");
	LISTEN(this, sock, 'message');
}

Socket.prototype.send = function(method, args)
{
	if (this.sock)
		this.sock.send(JSON.stringify({method:method, params:args}));
}

Socket.prototype.send_recv = function(self, method, args, func)
{
	if (!this.sock)
		return;
	this.el.addEventListener(method+'_resp', function(e){func.call(self, e.args);}, {once:true});
	this.sock.send(JSON.stringify({method:method, params:args}));
}

Socket.prototype.on_message = function(e)
{
	//~ console.log("MSG: "+e.data);
	const j = JSON.parse(e.data);
	var evt = new Event(j.method);
	evt.args = j.args
	this.el.dispatchEvent(evt);
}

Socket.prototype.on_close = function()
{
	console.log("Socket close");
	if (this.sock)
		this.sock.close();
	this.sock = null;
	this.el.innerHTML = "Disconnected";
	this.el.className = this.cls+' disconnected';
	if (this.auto_connect) {
		setTimeout(DO(this, function() {
			this.el.innerHTML += '<br>Trying to Reconnect'; 
			this.connect(this.path, DO(this, function(e) {
				console.log("Reconnected \(^o^)/");			
			}));
		}), 2000);
	}
}

Socket.prototype.on_unload = function()
{
	this.auto_connect = false;
	if (this.sock)
		this.sock.close();
	this.sock = null;
}
	
	

	
function Table(cls, rows, cols)
{
	this.nrows = rows;//classnames.length;
	this.ncols = cols;// classnames[0].length;
	this.el = EL('table', cls);
	for (var r=0; r < rows; r++ ) {
		this[r] = [];
		var row = EL('tr');
		for (var c =0; c < cols; c++) {
			var col = EL('td');
			//~ col.className = classnames[r][c];
			this[r].push(col);
			row.append(col);
		}
		this.el.append(row);
	}
}


function PageToEl(page, el)
{
	var left = 0;
	var top = 0;
	var cur = el;
	while(cur.offsetParent) {
		left -= cur.scrollLeft;
		top -= cur.scrollTop;
		cur = cur.parentNode;
	}
	cur = el;
	while(cur) {
		left += cur.offsetLeft - cur.scrollLeft;
		top += cur.offsetTop - cur.scrollTop;
		cur = cur.offsetParent;
	}
	//var scale = el.offsetWidth/1000.0;
	return [ (page.pageX - left), (page.pageY - top)];
}
	
function Slider(cls, pct)
{
	this.el = DIV("Slider "+cls);
	this.hnd = DIV("handle");
	//~ hnd.setAttribute("draggable", 'true');
	this.set(pct);// = pct;
	this.mvhnd = {target:null};
	
	LISTEN(this, this.el, 'change', function(e) {
		this.value = e.v;
	});
	
	function start (e1, touch) {
		//~ e1.preventDefault();
		function move(e) {
			//~ console.log(e);
			e.preventDefault();
			var max = this.el.clientWidth - this.hnd.clientWidth;
			var x = PageToEl(touch?e.touches[0] : e, this.el)[0] - this.hnd.clientWidth/2;
			var x = (x<0)? 0: ((x>max)? max: x);
			var evt = new Event("change");
			evt.v =  x/max;
			//~ console.log("screenX:"+screenX + "  max:"+max + "   x:" +x + "  v:"+evt.v);
			this.hnd.style.left=x+'px';
			this.el.dispatchEvent(evt);
		}
		move.call(this, e1);
		
		if (!this.mvhnd.target)
			this.mvhnd = THROTTLE(this, window, touch?"touchmove":"mousemove", 40, move);
		
		LISTEN(this, window,  touch?"touchend":"mouseup", {once:true}, function(e) {
			this.hnd.style.left = Math.round(this.value*100)+"%";
			STOP_LISTEN(this.mvhnd);
			var evt = new Event("commit");
			evt.v =  this.value;
			this.el.dispatchEvent(evt);
		});
	}
		
	LISTEN(this, this.el, 'touchstart', function(e) {start.call(this, e,true);});
	LISTEN(this, this.el, 'mousedown', function(e) {start.call(this, e,false);});

	this.el.append(this.hnd)
}

Slider.prototype.set = function(value)
{
	this.value = value;
	this.hnd.style.left = Math.round(this.value*100)+"%";
}

function POPUP (body, title="")
{
	if (body && !window.popup_panel) {
		window.popup_panel = DIV("Popup", [
			DIV("title", [
				DIV("msg"),
				BTN(this, "close", "\u2612", function(e) {POPUP(false);})
			]), 
			DIV("body")
		]);
		window.popup_glass =DIV("Popup-Glass");
		window.popup_glass.addEventListener("click", function(e) {POPUP(false);});
	}
	
	var pup = window.popup_panel;
	
	if (body) {
		document.body.append(window.popup_glass);
		var sw = window.innerWidth || document.documentElement.clientWidth || document.body.clientWidth;
		var sh = window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight;
		pup.style.maxWidth = Math.floor(sw*0.9)+"px";
		pup.style.maxHeight = Math.floor(sh*0.9)+"px";
		pup.firstChild.nextSibling.append(body);
		document.body.append(pup);
		var cw = pup.clientWidth;
		var ch = pup.clientHeight;
		pup.querySelector(".msg").innerHTML = title;
		pup.style.left = Math.round((sw-cw)/2)+"px";
		pup.style.top = Math.round((sh-ch)/2)+"px";
		
	} else {
		document.body.removeChild(window.popup_glass);
		document.body.removeChild(pup);
		var bdy = pup.firstChild.nextSibling
		while (bdy.firstChild)
			bdy.removeChild(bdy.firstChild);
	}
}

//~ function SEARCH(array, time)
//~ {
	//~ function rec(bottom, top) {
		//~ if (top-bottom <= 1)
			//~ return bottom;
		//~ var mid = ((top-bottom)>>1)+bottom;
		//~ if (time < array[mid])
			//~ return rec(bottom, mid);
		//~ else
			//~ return rec(mid, top);
	//~ }
	//~ return rec(0, array.length);
//~ }

function MULTIPART(url, dataURI, name, callback)
{
	//function dataURItoBlob(dataURI) {
	var bbb;
	if (dataURI instanceof File) {
		bbb = dataURI;
	} else {
		var binary = atob(dataURI.split(',')[1]);
		var array = [];
		for(var i = 0; i < binary.length; i++) {
			array.push(binary.charCodeAt(i));
		}
		bbb =  new Blob([new Uint8Array(array)], {type: 'image/jpeg'});
	}
	//}
	var fd = new FormData();
	fd.append('file', bbb, name);
	var xhr = new XMLHttpRequest();
	xhr.onreadystatechange = function() {
		if (xhr.readyState==4) {
			if (xhr.status==200) {
				callback(xhr.responseText);
			} else {
				alert(xhr.responseText);
			}
		}
	};
	xhr.open('POST', url, true);
	xhr.send(fd)
}

function GET(url, callback)
{
	var xhr = new XMLHttpRequest();
	xhr.open("GET",url, true);
	xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
	xhr.onreadystatechange = function () {
		if(xhr.readyState === XMLHttpRequest.DONE) {
			if( xhr.status === 200) {
				callback(xhr.responseText);
			} else {
				alert(xhr.responseText);
			}
		}
	};
	xhr.send();	
}

function RPC(method, args, callback, url="/rpc/play", timeout=5000)
{
	var xhr = new XMLHttpRequest();
	xhr.open("POST",url, true);
	if (timeout)
		xhr.timeout = timeout;
	xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
	xhr.onreadystatechange = function () {
		if(xhr.readyState === XMLHttpRequest.DONE) {
			if( xhr.status === 200) {
				resp = JSON.parse(xhr.responseText)
				callback(resp.result);
			} else {
				console.log("ERROR");
				console.log(xhr);
				//~ alert(xhr.responseText);
				callback();
			}
		}
	};
	xhr.ontimeout = function() {
		console.log("TIMEOUT");
		//~ alert("Not connected to the internet?\nSave your changes and try refreshing the browser.");
		callback();
	}
	xhr.send(JSON.stringify({method:method, params:args}));	

}

	
var DELAY = function* (clks)
{
	while(clks--)
		yield;
}

var BTN = function(self, cls, txt, func=null)
{
	var el = INPUT("button", cls);
	el.value = txt;
	LISTEN(self, el, "click", func);
	return el;
}

var DO = function(self, func)
{
	return function(e){func.call(self, e);}
};

var EL = function(type, className="", ns=null, html=null)
{
	var el = ns?document.createElementNS(ns, type) : document.createElement(type);
	if (className)
		el.setAttribute("class",className);
	if (html != null)
		el.innerHTML = html;

	return el;
};
function CHECKBOX(className, name)
{
	var el = INPUT('checkbox', className);
	el.setAttribute('name', name);
	return el;
}

function TEXTBOX(self, className="", txt="", func=null)
{
	var el = EL('input', className);
	el.setAttribute('type', 'text');
	el.value = txt;
	if (func)
		LISTEN(self, el, "change", func);
	return el;
}

function DROPDOWN(self, className="", options, sel=0, func=null)
{
	var el = EL("select", className);
	for (var o=0; o < options.length; ++o) {
		var opt = EL("option");
		opt.innerHTML = options[o];
		el.appendChild(opt);
	}
	el.value = options[sel];
	if (func)
		LISTEN(self, el, "change", func);
	return el;
}

var DIV =  function(className="", txt)
{
	var el = EL('div', className);
	if (Array.isArray(txt)) {
		for (var e=0; e < txt.length; ++e)
			el.appendChild(txt[e]);
	} else if (typeof txt === "string") {
		el.innerHTML = txt;
	}
	return el;
};

var INPUT = function(type, className="")
{
	var el = EL("input", className);
	el.setAttribute('type', type);
	return el;
}

var SPAN = function(className="", txt)
{
	var spn = EL('span', className);
	if (txt != undefined)
		spn.append(TXT(txt));
	return spn;
	
}


var TXT = function(txt)
{
	return document.createTextNode(txt);
};


function THROTTLE(self, el, event, ms, opts_func=null, func=null)
{
	var throttle = 0;
	
	var options = null;
	if (typeof opts_func === "function") {
		func = opts_func;
		options = {}
	} else {
		options = opts_func? opts_func : {};
	}
	func = func? func : self['on_'+event];
	
	function throttle_callback(e) {
		func.event = e;
		if (!(throttle ++)) {
			var fint = setInterval(DO(this, function() {
				if (!(--throttle)) {
					clearInterval(fint);
				} else {
					func.call(this, func.event);
					throttle = 1;
				}
			}), ms);
			func.call(this, func.event);
		}
	}
	var lfunc = DO(self, throttle_callback);
	el.addEventListener(event, lfunc, options);
	return {target:el, type:event, func:lfunc};
	
	//~ el.addEventListener(event, DO(self, throttle_callback), options);
}

function TIMER(self, ms, func)
{
	
	
	
	
}

function STOP_LISTEN(listen_obj)
{
	if (!listen_obj.target)
		return;
	listen_obj.target.removeEventListener(listen_obj.type, listen_obj.func);
	listen_obj.target = null;
}

var LISTEN = function(self, el, event, opts_func=null, func=null)
{
	var options = null;
	if (typeof opts_func === "function") {
		func = opts_func;
		options = {}
	} else {
		options = opts_func? opts_func : {};
	}
	func = DO(self, func? func : self['on_'+event]);
	el.addEventListener(event, func, options);
	return {target:el, type:event, func:func};
};

return {SLIDER: Slider, CHECKBOX:CHECKBOX, INPUT:INPUT, LISTEN:LISTEN, STOP_LISTEN:STOP_LISTEN, 
	MULTIPART:MULTIPART, GET:GET, THROTTLE:THROTTLE, EL:EL, DIV:DIV, TXT:TXT, TABLE:Table,PAGETOEL:PageToEl,
	DELAY:DELAY, SPAN:SPAN, DO:DO, BTN:BTN, RPC:RPC, DROPDOWN:DROPDOWN, TEXTBOX:TEXTBOX, POPUP:POPUP,
	SOCKET:Socket};
});

