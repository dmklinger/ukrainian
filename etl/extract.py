import bz2
import os
import requests
import json
from bs4 import BeautifulSoup

from dictionary import Word

os.makedirs('data', exist_ok=True)

try:
	with open('data/wiktionary_raw_data.json', 'r', encoding='utf-8') as f:
		wiktionary_cache = json.loads(f.read())
except:  # does not exist yet
	wiktionary_cache = {}

cyrillic = "ЄІЇАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдежзийклмнопрстуфхцчшщъыьэюяєії"

def get_ontolex():
	session = requests.session()
	print('downloading latest ontolex data from dbnary')
	with session.get('http://kaiko.getalp.org/static/ontolex/latest/en_dbnary_ontolex.ttl.bz2', stream=True) as f:
		data = bz2.BZ2File(f.raw).read()
	print('decompressing')
	with open('data/raw_dbnary_dump.ttl', 'wb+', encoding='utf-8') as f:
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


def get_wiktionary_word(word, use_cache=True):
	session = requests.session()
	if word in wiktionary_cache and use_cache:
		article = wiktionary_cache[word]
	else:
		article = session.get(
			f'https://en.wiktionary.org/w/api.php?action=parse&page={word}&prop=text&formatversion=2&format=json'
		).json()['parse']['text']
		wiktionary_cache[word] = article
	article = BeautifulSoup(article, 'lxml')

	results = []

	word_name = article.find_all('strong', {'class': 'Cyrl headword'}, lang='uk')
	for word_pointer in word_name:
		accented_name = word_pointer.text  # name
		w = Word(accented_name)
		pos_pointer = word_pointer.find_previous(['h3', 'h4'])
		pos = pos_pointer.span.text.lower()
		def_pointer = word_pointer.find_next('ol')
		ds = def_pointer.find_all('li')
		bad_stuff = def_pointer.find_all('ul') + def_pointer.find_all('span', class_ = 'HQToggle')
		for bs in bad_stuff:
			bs.decompose()
		for d in ds:
			if d.dl:
				d.dl.decompose()
			w.add_definition(pos, d.text.strip())
		results.append(w)
	return results

def dump_wiktionary_cache():
	with open(f'data/wiktionary_raw_data.json', 'w+', encoding='utf-8') as f:
		f.write(json.dumps(wiktionary_cache, ensure_ascii=False))

def get_frequency_list():
	parts_of_speech = {
		'': None, 
		'абревіатура': 'abbreviation', 
		'вигук': 'interjection', 
		'дієсл.': 'verb', 
		'займ.': 'pronoun',  # inflected
		'займ.-прикм.': 'pronoun',  # impersonal
		'займ.-ім.': 'pronoun',  # personal
		'прийм.': 'preposition', 
		'прикметник': 'adjective', 
		'прислівн.': 'adverb', 
		'присудкова форма': 'predicate', 
		'сполучн.': 'conjugation', 
		'форма на -но/-то': None,  # unclear 
		'част.': 'particle', 
		'числ.': 'numeral', 
		'ім. ж. р.': 'noun',  # female
		'ім. множ.': 'noun',  # plural
		'ім. с. р.': 'noun',  # neuter
		'ім. ч. р.': 'noun',  # male
	}
	session = requests.session()
	with session.get('http://ukrkniga.org.ua/ukr_rate/hproz_92k_lex_dict_orig.csv', stream=True) as f:
		f.encoding = 'utf-8'
		data = [row.split(';')[0:3] for row in f.text.split('\n')[1:-1]]
	data = [{'rank': x[0], 'word': x[1], 'pos': parts_of_speech[x[2]]} for x in data]
	with open(f'data/frequencies.json', 'w+', encoding='utf-8') as f:
		f.write(json.dumps(data, indent=2, ensure_ascii=False))