#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 25 00:03:01 2018
@author: Yves
"""

import time
import datetime
import hashlib
import json
import pickle
from flask import Flask, jsonify, request,send_file,after_this_request
import os.path
import os
import signal
import sys
import requests
from uuid import uuid4
from urllib.parse import urlparse
import tempfile
from werkzeug.utils import secure_filename
import base64
import shutil
import weakref

#Change the following
#Domainname give the IP or the domain name linked to your ip (78.193.64.188 or guiltycore.fr )
domainName = 'http://guiltycore.fr'
#Give the port you want to use for this blockchain
#Don't forget to open the port.
PORT = 5000
upChainFiles="/var/www/html/"



port = str(PORT)
linkDomain=domainName+":"+port
class BlockChain:
	def __init__(self):
		self.chain = []
		self.create_block(proof=1, previous_hash='0', data='No data', name='No name')
		self.nodes = set()
		if not os.path.exists('./upload'):
			os.makedirs('./upload')

	def create_block(self, proof, previous_hash, data, name):
		block = {
			'index': len(self.chain) + 1,
			'timestamp': str(datetime.datetime.now()),
			'name': name,
			'data': data,
			'proof': proof,
			'previous_hash': previous_hash
		}
		self.chain.append(block)
		return block

	def get_previous_block(self):
		return self.chain[-1]

	def proof_of_work(self, previous_proof):
		new_proof = 1
		check_proof = False
		while not check_proof:
			hash_operation = hashlib.sha256(str(new_proof ** 2 - previous_proof ** 2).encode()).hexdigest()
			if hash_operation[:4] == '0000':
				check_proof = True
			else:
				new_proof += 1
		return new_proof

	def hash(self, block):
		encoded_block = json.dumps(block, sort_keys=True).encode()
		return hashlib.sha256(encoded_block).hexdigest()

	def is_chain_valid(self, chain):
		previous_block = chain[0]
		block_index = 1
		while block_index < len(chain):
			block = chain[block_index]
			if block['previous_hash'] != self.hash(previous_block):
				return False
			previous_proof = previous_block['proof']
			proof = block['proof']
			hash_operation = hashlib.sha256(str(proof ** 2 - previous_proof ** 2).encode()).hexdigest()
			if hash_operation[:4] != '0000':
				return False
			previous_block = block
			block_index += 1

		return True

	def serialize(self,a='',b='',c=''):
		w = pickle.dumps(self.chain)
		y = pickle.dumps(self.nodes)
		x = open(upChainFiles+'chain.bc', 'wb')
		z = open(upChainFiles+'nodes.bc','wb')
		x.write(w)
		z.write(y)
		print("Blockchain serialized")

	@staticmethod
	def deserialize():
		rt = BlockChain()
		if (os.path.exists(upChainFiles+'chain.bc')):
			rt.chain = pickle.load(open(upChainFiles+'chain.bc', 'rb'))
		if (os.path.exists(upChainFiles+'nodes.bc')):
			rt.nodes = pickle.load(open(upChainFiles+'nodes.bc', 'rb'))
		return rt

	def add_node(self, address):
		parsed_url = urlparse(address)
		self.nodes.add(parsed_url.netloc)

	def replace_chain(self):
		network = self.nodes
		longest_chain = None
		max_length = len(self.chain)
		for node in network:
			response = requests.get(f'http://{node}/get_chain')
			if (response.status_code == 200):
				length = response.json()['length']
				chain = response.json()['chain']
				if length > max_length and self.is_chain_valid(chain):
					max_length = length
				longest_chain = chain
		if longest_chain:
			self.chain = longest_chain
			return True
		return False


class FileRemover(object):
	def __init__(self):
		self.weak_references = dict()  # weak_ref -> filepath to remove

	def cleanup_once_done(self, response, filepath):
		wr = weakref.ref(response, self._do_cleanup)
		self.weak_references[wr] = filepath

	def _do_cleanup(self, wr):
		filepath = self.weak_references[wr]
		print('Deleting %s' % filepath)
		shutil.rmtree(filepath, ignore_errors=True)


file_remover = FileRemover()

app = Flask(__name__)
# Creating an address for the node on Port 5000
node_address = str(uuid4()).replace('-', '')

# Creating a Blockchain

UPLOAD_FOLDER = './upload/'
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

blockchain = BlockChain.deserialize()


def close_running_threads(a='',b=''):
	print("Hey")
	blockchain.serialize()
	print("Chainblock serialized!")
	sys.exit(0)

# Mining a new block
@app.route('/mine_block', methods=['POST'])
def mine_block():
	response = {
		'message': 'Case not handled',
		'timestamp': str(datetime.datetime.now())
	}
	if 'file' not in request.files:
		response = {
			'message': 'No file',
			'timestamp': str(datetime.datetime.now())
		}
		return response, 201
	else:

		file = request.files['file']
		# if user does not select file, browser also
		# submit a empty part without filename
		if file.filename == '':
			response = {
				'message': 'No selected file',
				'timestamp': str(datetime.datetime.now())
			}
			return response, 201
		elif file:
			data = file.read()
			base64_data = base64.b85encode(data)
			previous_block = blockchain.get_previous_block()
			previous_proof = previous_block['proof']
			proof = blockchain.proof_of_work(previous_proof)
			previous_hash = blockchain.hash(previous_block)
			block = blockchain.create_block(proof, previous_hash, data=base64_data.decode('UTF-8'), name=file.filename)
			end=""
			if("." in block["name"]):
				end="."+str(block["name"]).split(".")[1]
			response = {
				'URL': linkDomain + '/' + blockchain.hash(block)+end,
				'timestamp': block['timestamp']
			}
			for node in blockchain.nodes:
				requests.get(f'http://{node}/replace_chain')
			return jsonify(response), 400
	return response, 201


# Getting the full Blockchain
@app.route('/get_chain', methods=['GET'])
def get_chain():
	response = {
		'chain': blockchain.chain,
		'length': len(blockchain.chain)
	}
	return jsonify(response), 200


# Checking if the block chain is valid

@app.route('/is_valid', methods=['GET'])
def is_valid():
	is_valid = blockchain.is_chain_valid(blockchain.chain)
	if (is_valid):
		response = {'message': 'All good. The Blockchain is valid.'}
	else:
		response = {'message': 'Houston, we have a problem. The Blockchain is not valid.'}
	return jsonify(response), 200


# Part 3 - Decentralizing our Blockchain
@app.route('/replace_chain', methods=['GET'])
def replace_chain():
	is_chain_replaced = blockchain.replace_chain()
	if is_chain_replaced:
		response = {
			'message': 'The node had different chains so the chain was replaced by the longest one.',
			'new_chain': blockchain.chain
		}
	else:
		response = {
			'message': 'All good. The Blockchain is the largest one.',
			'actual_chain': blockchain.chain
		}
	return jsonify(response), 200


# Connection new nodes
@app.route('/connect_node', methods=['POST'])
def connect_node():
	json = request.get_json()
	nodes = json.get('nodes')
	if nodes is None:
		return "Node node", 400
	nod = set()
	for node in nodes:
		r = requests.get(f'{node}/get_chain')
		url = (urlparse(node).netloc)
		if r.status_code == 200 and  url not in blockchain.nodes and not node == domainName+":"+port:
			blockchain.add_node(node)
			nod.add(node)

	if not len(nod) is 0:
		tt=blockchain.nodes.copy()
		for node in tt:
			tab = list(blockchain.nodes.copy())
			tab.remove(node)
			for i in range(0,len(tab)):
				tab[i]='http://'+tab[i]
			tab.append(domainName + ":" + port)

			new_json = {"nodes": list(tab)}
			requests.post(f'http://{url}/connect_node', json=new_json)

	response = {
		'message': 'All nodes are now connected. The upChain now contains the following nodes',
		'total_nodes': list(blockchain.nodes)
	}
	return jsonify(response), 201

# Historic blockchain
@app.route('/blockchain_historic', methods=['GET'])
def blockchain_historic():
	response = []
	for block in blockchain.chain:
		if (block['previous_hash'] != '0'):
			if (domainName is not None):
				spl=""
				if '.' in block["name"]:
					spl = '.'+(str(block["name"]).split("."))[1]
				me = secure_filename(blockchain.hash(block) + spl)
				duo = {
					"name": block["name"],
					"URL": linkDomain + '/'+blockchain.hash(block)+spl
				}
			else:
				duo = {"name": block["name"]}
			response.append(duo)
	return jsonify(response), 201


# Get images by hash
@app.route('/<path:path>')
def get_image(path):
	if not ('/' in path or '\\' in path):

		hash = path
		if '.' in hash:
			hash=hash.split('.')[0]
		block=None
		for bl in blockchain.chain:
			if(blockchain.hash(bl)==hash and block is None):
				block=bl
		if block is not None:
			file_remover = FileRemover()
			tempdir = tempfile.mkdtemp()
			file_content= base64.b85decode(block["data"].encode("UTF-8"))
			print(tempdir)
			fl=open(tempdir+block["name"],'wb')
			fl.write(file_content)
			fl.close()
			resp=send_file(tempdir+block["name"], block["name"])
			file_remover.cleanup_once_done(resp, tempdir)

		return resp
	return "File not found",404



# Running the app

def termtoint(a='',b=''):
        exit(0)
# Running the app
signal.signal(signal.SIGTERM,termtoint)
signal.signal(signal.SIGINT,blockchain.serialize)
if not os.fork():
	if __name__ == "__main__":
		app.run(host='0.0.0.0', port=PORT, threaded=True)

