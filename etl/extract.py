import bz2
import os
import requests
import json
from collections import defaultdict
from bs4 import BeautifulSoup, NavigableString

from dictionary import Word

os.makedirs('data', exist_ok=True)

try:
	with open('data/wiktionary_raw_data.json', 'r', encoding='utf-8') as f:
		wiktionary_cache = json.loads(f.read())
except:  # does not exist yet
	wiktionary_cache = {}


def get_ontolex(use_cache=True):
	if use_cache and os.path.exists('data/raw_dbnary_dump.ttl'):
		return
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

	def clean_tag(tag):
		res = ''
		for child in tag.contents:
			if isinstance(child, NavigableString):
				res += str(child)
			elif child.name in ('sup', 'sub'):
				res += str(child)
			elif child.name in ('ol', 'ul'):
				None  # in this house we say NO to recursion
			elif child.name in ('li'):
				res += clean_tag(child) + ','
			else:
				res += clean_tag(child)
		return res

	results = []

	word_name = article.find_all('strong', {'class': 'Cyrl headword'}, lang='uk')
	for word_pointer in word_name:
		bad_stuff = word_pointer.find_all(class_='reference')
		for bs in bad_stuff:
			bs.decompose()
		accented_name = word_pointer.text.strip()  # name
		word_info = word_pointer.find_next('span', {'class': 'gender'})
		if word_info is not None:
			word_info = word_info.text.strip()
		w = Word(accented_name)
		pos_pointer = word_pointer.find_previous(['h3', 'h4'])
		pos = pos_pointer.span.text.lower()
		def_pointer = word_pointer.find_next('ol')
		ds = def_pointer.find_all('li')
		bad_stuff = def_pointer.find_all('span', class_='HQToggle') \
			+ def_pointer.find_all('abbr') \
			+ def_pointer.find_all(lang='uk-Latn') \
			+ def_pointer.find_all(class_='mention-gloss-paren annotation-paren') \
			+ def_pointer.find_all(class_='mention-gloss-double-quote') \
			+ def_pointer.find_all(class_='nyms synonym') \
			+ def_pointer.find_all(class_='citation-whole') \
			+ def_pointer.find_all(class_='plainlinks')
		for bs in bad_stuff:
			bs.decompose()
		for d in ds:	
			glosses = [g.extract().text.strip() for g in d.find_all(class_='mention-gloss')]
			if d.dl:
				d.dl.decompose()
			d = clean_tag(d)
			d = ' '.join(d.split())
			d = d.replace(' ,', ',')
			d = d.replace(' .', '.')
			d = d.replace(' :', ':')
			d = d.replace(' :', ':')
			d = d.replace(',:', ':')
			d = d.rstrip(',.:').strip()
			if len(d) > 0:
				w.add_definition(pos, d)
			if len(glosses) > 0:
				for g in glosses:
					w.add_definition(pos, g)
		inflection_pointer = word_pointer.parent
		if pos != 'verb':
			inflection_pointer = inflection_pointer.find_next('span', text='Declension')
		else:
			inflection_pointer = inflection_pointer.find_next('span', text='Conjugation')
		table = None
		if inflection_pointer is not None:
			table = inflection_pointer.find_next('table', {'class': 'inflection-table'}) 
		if table is None and inflection_pointer is not None:
			table = inflection_pointer.find_next('table', {'class': 'inflection-table inflection inflection-uk inflection-verb'})
		if table and len(w.usages.keys()) > 0:
			forms = parse_wiktionary_table(accented_name, table) 
			if forms:
				w.add_forms(list(w.usages.keys())[0], forms)
		results.append(w)
	return results


def parse_wiktionary_table(w, inflections):

	def parse_verb(items):
		forms = defaultdict(lambda: [])
		for span in items:
			tense, number, gender, person, participle = None, None, None, None, None
			tense_info = span['class'][3].replace('-form-of', '').split('|')
			for t in tense_info:
				if t in ('inf', 'pres', 'past', 'fut', 'imp'):
					tense = t
				if t in ('m', 'f', 'n'):
					gender = t
				if t in ('1', '2', '3'):
					person = t
				if t in ('s', 'p'):
					number = t
				if t in ('impers', 'act', 'pass', 'adv'):
					participle = {'impers': 'imp', 'act': 'act', 'pass': 'pas', 'adv': 'adv'}[t]
			if tense == 'inf':
				form = tense
			elif participle is not None:
				form = f"{tense} {participle} pp"
			elif tense in ('pres', 'fut', 'imp'):
				form = f'{tense} {person}{number}'
			elif tense == 'past':
				if number == 's':
					form = f'past {gender}s'
				else:
					form = 'past p'
			forms[form].append(span.text.strip())
		forms = dict(forms)
		return forms

	def parse_noun(items):
		forms = defaultdict(lambda: [])
		for span in items:
			case_info = span['class'][3].replace('-form-of', '').split('|')
			forms[f"{case_info[0]} n{case_info[1]}"].append(span.text.strip())
		forms = dict(forms)
		return forms

	def parse_adj(items):
		forms = defaultdict(lambda: [])
		for span in items:
			case_info = span['class'][3].replace('-form-of', '').split('|')
			if case_info[0] in ('an', 'in'):
				if case_info[0] == 'an':
					case_info = [None, None, None, None, None]
				else:
					case_info = case_info[1:]
			if case_info[1] == 'p':
				form = f"{case_info[0]} ap"
				forms[form].append(span.text.strip())
			elif case_info[1] == 'm//n':
				form = f"{case_info[0]} am"
				forms[form].append(span.text.strip())
				form = f"{case_info[0]} an"
				forms[form].append(span.text.strip())
			else:
				form = f"{case_info[0]} af"
				forms[form].append(span.text.strip())
		forms = dict(forms)
		return forms

	def parse_pronoun(word):
		nom = ['я', 'ти', 'він', 'воно́', 'вона́', 'ми', 'ви', 'вони́']
		gen = ['мене́', 'тебе́', 'його́, ньо́го', 'його́, ньо́го*', 'її́, не́ї', 'нас', 'вас', 'їх, них*']
		dat = ['мені́', 'тобі́', 'йому́', 'йому́', 'їй', 'нам', 'вам', 'їм']
		acc = ['мене́', 'тебе́', 'його́, ньо́го', 'його́, ньо́го*', 'її́, не́ї', 'нас', 'вас', 'їх, них*']
		ins = ['мно́ю', 'тобо́ю', 'ним', 'ним', 'не́ю', 'на́ми', 'ва́ми', 'ни́ми']
		loc = ['мені́', 'тобі́', 'ньо́му, нім', 'ньо́му, нім', 'ній', 'нас', 'вас', 'них']
		index = {e.replace('́', ''): i for i, e in enumerate(nom)}
		word = word.replace('́', '')
		if word not in index:
			return None
		forms = defaultdict(lambda: [])
		forms['nom n'] += nom[index[word]].split(', ')
		forms['gen n'] += gen[index[word]].split(', ')
		forms['dat n'] += dat[index[word]].split(', ')
		forms['acc n'] += acc[index[word]].split(', ')
		forms['ins n'] += ins[index[word]].split(', ')
		forms['loc n'] += loc[index[word]].split(', ')
		forms = dict(forms)
		return forms

	items = [span for span in inflections.find_all('span', {'class': 'form-of', 'lang': 'uk'})]
	cat = None
	for i in items:
		row = i['class'][3].replace('-form-of', '').split('|')
		if cat is None and row[0] == 'inf':
			cat = 'verb'
		elif cat is None and row[1] == 'm//n':
			cat = 'adj'
		elif cat is None and row[1] == 's':
			cat = 'noun'
	if len(items) == 0:  # maybe a pronoun:
		items = [span for span in inflections.find_all('span', {'class': 'Cyrl', 'lang': 'uk'})]
		if len(items) > 0:
			cat = 'pronoun'
	forms = None
	if cat == 'verb':
		forms = parse_verb(items)
	if cat == 'noun':
		forms = parse_noun(items)
	if cat == 'adj':
		forms = parse_adj(items)
	if cat == 'pronoun':
		forms = parse_pronoun(w)

	return forms


def dump_wiktionary_cache():
	with open(f'data/wiktionary_raw_data.json', 'w+', encoding='utf-8') as f:
		f.write(json.dumps(wiktionary_cache, ensure_ascii=False))


def get_frequency_list():
	try:
		with open('data/frequencies.json', 'r', encoding='utf-8') as f:
			data = json.loads(f.read())
	except:  # does not exist yet	
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
		frequency_dict = defaultdict(lambda: {})
		with session.get('http://ukrkniga.org.ua/ukr_rate/hproz_92k_lex_dict_orig.csv', stream=True) as f:
			f.encoding = 'utf-8'
			data = [row.split(';')[0:3] for row in f.text.split('\n')[1:-1]]
		for x in data:
			frequency_dict[
				x[1]  # word
			][
				parts_of_speech[x[2]]  # part of speech
			] = x[0]  # rank
		with open(f'data/frequencies.json', 'w+', encoding='utf-8') as f:
			f.write(json.dumps(frequency_dict, indent=2, ensure_ascii=False))
	return data