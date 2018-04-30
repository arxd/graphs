import tornado
import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.httpserver

import json, sys

PORT = int(sys.argv[1])
STATICDIR = "./"
from graphlib import GraphDB, Graph, NEATO 
DB = GraphDB(sys.argv[2])


class BaseHandler(tornado.web.RequestHandler):
	def resp(self, code, type):
		self.set_status(code)
		self.set_header("Content-Type", type)
		self.set_header("Cache-Control","no-cache, must-revalidate")
		self.set_header("Pragma", "no-cache")
		self.set_header("Expires", "Sat, 26 Jul 1997 05:00:00 GMT")
		#self.end_headers()
	
	def error(self):
		self.resp(400, "text/html")
		self.write("Nothing to see here.  Move along.".encode('utf8'))
	
	def load_app(self, title, jsmain, css, js=""):
		self.resp(200, "text/html")
		html = """<!DOCTYPE html>
				<html>
				<head>
				<meta charset="UTF-8">
				<meta name="viewport" content="width=device-width, initial-scale=1.0">
				<title>%s</title>
				"""%(title)
		for c in css:
			html+= '<link rel="stylesheet" type="text/css" href="%s.css">\n'%c
		
		html+='<script data-main="%s" src="require.js"></script>'%jsmain
		html+='<script>%s</script>'%js
		html+='</head><body></body></html>'
		self.write(html.encode('utf8'))
		self.finish()
		

class RPCWebSocket(tornado.websocket.WebSocketHandler):
	def open(self):
		print "Websocket Opened"

	def on_close(self):
		print "Websocket closed"

	def on_message(self, message):
		args = json.loads(message)
		method = args[u"method"]
		rpc_func =  getattr(self, 'rpc_%s'%(method))
		result = rpc_func(*(args[u"params"]))
		if result != None:
			self.write_message(json.dumps({'method':method+'_resp', 'args':result}))

	def rpc_lookup(self, graphs):
		print("--------------------------------")
		print("Lookup: %d graphs"%len(graphs))
		resp = []
		for g in graphs:
			r = Graph(g)
			r.symmetry()
			print(r.str())
			resp.append({'esym':{"%d-%d"%(k):v for k,v in r.edge_sym.items()}, 'nsym':r.node_sym})
		
		return resp

class FileServer(BaseHandler):
	def get(self, filename, type):
		#~ ext = filename[filename.rfind('.')+1:]
		print("Load %s (%s)"%(filename, type))
		#~ print(os.path.exists(STATICDIR+filename))
		try:
			type = {
			'js':'application/javascript', 
			'css':'text/css', 
			'png':'image/png',
			'jpg':'image/jpeg',
			'gif':'image/gif',
			'mp3':'audio/mpeg'}[type]
		except:
			return self.error()
			
		f=open(STATICDIR+filename,'rb')
		self.resp(200, type)
		self.write(f.read())
		self.finish()
		f.close()


class MainServer(BaseHandler):
	def get(self):
		return self.load_app("Editor", 'editor', ['editor'])
	

application = tornado.web.Application([
	(r"/.*?([a-zA-Z_0-9]+\.(js|css|png|jpg))", FileServer),
	(r"/", MainServer),
	#~ (r"/manual/(.*)", ManualPlay),
	#~ (r"/perform/(.*)", PerformPlay),
	(r"/ctrl", RPCWebSocket),
	#~ (r"/.*", BaseHandler)
	])

server =  tornado.httpserver.HTTPServer(application)
server.listen(PORT)
io_loop = tornado.ioloop.IOLoop.current()

#~ tornado.ioloop.PeriodicCallback(light_update, 30).start()
print("Listening...")
io_loop.start()
print("Closing...")
DB.close()