import bz2
import os
import requests

os.makedirs('data', exist_ok=True)


def get_ontolex():
	session = requests.session()
	print('downloading latest ontolex data from dbnary')
	with session.get('http://kaiko.getalp.org/static/ontolex/latest/en_dbnary_ontolex.ttl.bz2', stream=True) as f:
		data = bz2.BZ2File(f.raw).read()
	print('decompressing')
	with open('data/raw_dbnary_dump.ttl', 'wb+') as f:
		f.write(data)
	print('decompressing finished')


def get_lemmas():
	session = requests.session()

	def add_words(words, results):
		for word in results['query']['categorymembers']:
			title = word['title']
			if 'Category' not in title:
				words.append(title)

	words = []

	results = session.get('https://en.wiktionary.org/w/api.php?action=query&list=categorymembers&cmtitle=Category:Ukrainian_lemmas&format=json&cmlimit=max').json()
	add_words(words, results)

	while 'continue' in results:
		cmcontinue = results['continue']
		results = session.get(f'https://en.wiktionary.org/w/api.php?action=query&list=categorymembers&cmtitle=Category:Ukrainian_lemmas&format=json&cmlimit=max&cmcontinue={cmcontinue}').json()
		add_words(words, results)
	
	return words
