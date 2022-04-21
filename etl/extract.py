import bz2
import os
import requests
import json
from urllib import parse
from collections import defaultdict
from copy import deepcopy
from bs4 import BeautifulSoup, NavigableString

from dictionary import Word, cyrillic

os.makedirs('data', exist_ok=True)

session = requests.session()

try:
	with open('data/wiktionary_raw_data.json', 'r', encoding='utf-8') as f:
		wiktionary_cache = json.loads(f.read())
except:  # does not exist yet
	wiktionary_cache = {}

def get_viewstate(bs=None):
	if bs is None:
		url = "https://lcorp.ulif.org.ua/dictua/dictua.aspx"
		req = session.get(url)
		data = req.text
		bs = BeautifulSoup(data, features='lxml')
	return (
		bs.find("input", {"id": "__VIEWSTATE"}).attrs['value'],
		bs.find("input", {"id": "__VIEWSTATEGENERATOR"}).attrs['value'],
		bs.find("input", {"id": "__EVENTVALIDATION"}).attrs['value'],
	)

vs, vsg, ev = get_viewstate()

try:
	with open('data/inflection_raw_data.json', 'r', encoding='utf-8') as f:
		inflection_cache = json.loads(f.read())
except:
	inflection_cache = {}


def get_ontolex(use_cache=True):
	if use_cache and os.path.exists('data/raw_dbnary_dump.ttl'):
		return
	print('downloading latest ontolex data from dbnary')
	with session.get('http://kaiko.getalp.org/static/ontolex/latest/en_dbnary_ontolex.ttl.bz2', stream=True) as f:
		data = bz2.BZ2File(f.raw).read()
	print('decompressing')
	with open('data/raw_dbnary_dump.ttl', 'wb+', encoding='utf-8') as f:
		f.write(data)
	print('decompressing finished')


def get_lemmas():
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
	for word_pointer in word_name[::-1]:
		bad_stuff = word_pointer.find_all(class_='reference')
		for bs in bad_stuff:
			bs.decompose()
		accented_name = word_pointer.text.strip()  # name
		word_info = word_pointer.parent.find('span', {'class': 'gender'})
		if word_info is not None:
			word_info = word_info.text.strip()
		w = Word(accented_name)
		pos_pointer = word_pointer.find_previous(['h3', 'h4'])
		pos = pos_pointer.span.text.lower()
		def_pointer = word_pointer.find_next('ol')
		ds = def_pointer.find_all('li')
		bad_stuff = def_pointer.find_all('span', class_='HQToggle') \
			+ def_pointer.find_all('abbr') \
			+ def_pointer.find_all('ul') \
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
				w.add_info(Word.replace_pos(pos), word_info)
			if len(glosses) > 0:
				for g in glosses:
					w.add_definition(pos, g)
					w.add_info(Word.replace_pos(pos), word_info)
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
			forms, form_type = parse_wiktionary_table(accented_name, table) 
			w.add_forms(Word.replace_pos(pos), forms, form_type)
			table.extract()
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
				if t in ('impers', 'act', 'pass', 'adv') and participle is None:
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
				case_info = case_info[1:]
			if case_info[1] == 'p':
				form = f"{case_info[0]} ap"
				forms[form].append(span.text.strip())
			elif case_info[1] == 'm//n':
				form = f"{case_info[0]} am"
				forms[form].append(span.text.strip())
				form = f"{case_info[0]} an"
				forms[form].append(span.text.strip())
			elif case_info[1] == 'm':
				form = f"{case_info[0]} am"
				forms[form].append(span.text.strip())
			elif case_info[1] == 'n':
				form = f"{case_info[0]} an"
				forms[form].append(span.text.strip())
			else:
				form = f"{case_info[0]} af"
				forms[form].append(span.text.strip())
		forms = dict(forms)
		return forms

	def parse_pronoun(word):
		nom = ['я', 'ти', 'він', 'воно́', 'вона́', 'ми', 'ви', 'вони́']
		gen = ['мене́', 'тебе́', 'його́, ньо́го', 'його́, ньо́го', 'її́, не́ї', 'нас', 'вас', 'їх, них*']
		dat = ['мені́', 'тобі́', 'йому́', 'йому́', 'їй', 'нам', 'вам', 'їм']
		acc = ['мене́', 'тебе́', 'його́, ньо́го', 'його́, ньо́го', 'її́, не́ї', 'нас', 'вас', 'їх, них*']
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
	form_type = None
	if cat == 'verb':
		form_type = 'verb'
		forms = parse_verb(items)
	if cat == 'noun':
		form_type = 'noun'
		forms = parse_noun(items)
	if cat == 'adj':
		form_type = 'adj'
		forms = parse_adj(items)
	if cat == 'pronoun':
		form_type = 'noun'
		forms = parse_pronoun(w)

	return forms, form_type


def dump_wiktionary_cache():
	with open(f'data/wiktionary_raw_data.json', 'w+', encoding='utf-8') as f:
		f.write(json.dumps(wiktionary_cache, ensure_ascii=False))


def scrape_inflection(word):
	
	def parse_verbs(rows):
		forms = {}
		last_seen_type = None
		current_tense = None
		for row in rows:
			if row[0] == 'Інфінітив':
				forms['inf'] = row[1]
			if 'Наказовий' in row[0]:
				current_tense = 'imp'
			if 'МАЙБУТНІЙ' in row[0]:
				current_tense = 'fut'
			if 'ТЕПЕРІШНІЙ' in row[0]:
				current_tense = 'pres'
			if 'МИНУЛИЙ' in row[0]:
				current_tense = 'past'
			if row[0] == '1 особа':
				if current_tense == 'imp':
					forms['imp 1p'] = row[2]
				else:
					forms[f'{current_tense} 1s'] = row[1]
					forms[f'{current_tense} 1p'] = row[2]
			if row[0] == '2 особа':
				forms[f'{current_tense} 2s'] = row[1]
				forms[f'{current_tense} 2p'] = row[2]
			if row[0] == '3 особа':
				forms[f'{current_tense} 3s'] = row[1]
				forms[f'{current_tense} 3p'] = row[2]
			if 'чол.' in row[0]:
				forms['past ms'] = row[1]
				forms['past p'] = row[2]
			if 'жін.' in row[0]:
				forms['past fs'] = row[1]
			if 'сер.' in row[0]:
				forms['past ns'] = row[1]
			if row[0] in ('Активний дієприкметник', 'Пасивний дієприкметник', 'Дієприслівник', 'Безособова форма'):
				last_seen_type = row[0]
			elif last_seen_type is not None:
				form = current_tense + ' ' + {
					'Активний дієприкметник': 'act pp',
					'Пасивний дієприкметник': 'pas pp',
					'Дієприслівник': 'adv pp',
					'Безособова форма': 'imp pp'
				}[last_seen_type]
				forms[form] = row[0]
		for f in list(forms.keys()):
			if forms[f] == '':
				del forms[f]
		return forms

	def parse_nouns(rows):
		forms = {}
		for row in rows:
			case = None
			if row[0] == 'називний':
				case = 'nom'
			if row[0] == 'родовий':
				case = 'gen'
			if row[0] == 'давальний':
				case = 'dat'
			if row[0] == 'знахідний':
				case = 'acc'
			if row[0] == 'орудний':
				case = 'ins'
			if row[0] == 'місцевий':
				case = 'loc'
			if row[0] == 'кличний':
				case = 'voc'
			if case is not None:
				if len(row) > 2:
					forms[f'{case} ns'] = row[1]
					forms[f'{case} np'] = row[2]
				else:
					forms[f'{case} n'] = row[1]
		return forms

	def parse_adjectives(rows):
		forms = {}
		for row in rows:
			case = None
			if row[0] == 'називний':
				case = 'nom'
			if row[0] == 'родовий':
				case = 'gen'
			if row[0] == 'давальний':
				case = 'dat'
			if row[0] == 'знахідний':
				case = 'acc'
			if row[0] == 'орудний':
				case = 'ins'
			if row[0] == 'місцевий':
				case = 'loc'
			if row[0] == 'кличний':
				case = 'voc'
			if case is not None:
				forms[f'{case} am'] = row[1]
				forms[f'{case} af'] = row[2]
				forms[f'{case} an'] = row[3]
				forms[f'{case} ap'] = row[4]
		return forms

	# initial search
	data={
		'ctl00$ContentPlaceHolder1$ScriptManager1': 'ctl00$ContentPlaceHolder1$UpdText|ctl00$ContentPlaceHolder1$search', 
		'__EVENTTARGET': '',
		'__EVENTARGUMENT': '',
		'__VIEWSTATE': parse.quote(vs, safe=""),
		'__VIEWSTATEGENERATOR': parse.quote(vsg, safe=""),
		'__EVENTVALIDATION': parse.quote(ev, safe=""),
		'ctl00$ContentPlaceHolder1$tsearch': parse.quote(f'{word}', safe=""),
		'ctl00$ContentPlaceHolder1$search.x': '0',
		'ctl00$ContentPlaceHolder1$search.y': '0'
	}
	data = '&'.join([f"{key}={val}" for key, val in data.items()])

	result = session.post(
		'https://lcorp.ulif.org.ua/dictua/dictua.aspx', 
		headers={
			'Content-Type': 'application/x-www-form-urlencoded',
			'Origin': 'https://lcorp.ulif.org.ua',
			'Referer': 'https://lcorp.ulif.org.ua/dictua/dictua.aspx'
		},
		data=data
	)
	result = BeautifulSoup(result.text, features='lxml')
	index = result.find('table', id='ctl00_ContentPlaceHolder1_dgv')
	other_words = index.find_all('a') if index else []

	# subsequent searches
	results = []
	for i, a in enumerate(other_words):
		if a.text.replace('́','') == word.replace('́',''):
			# if we get here, we found it, even if we can't find results
			data={
				'ctl00$ContentPlaceHolder1$ScriptManager1': 'ctl00$ContentPlaceHolder1$UpdText|ctl00$ContentPlaceHolder1$dgv', 
				'__EVENTTARGET': parse.quote('ctl00$ContentPlaceHolder1$dgv', safe=""),
				'__EVENTARGUMENT': parse.quote(f'Select${i}', safe=""),
				'__VIEWSTATE': parse.quote(vs, safe=""),
				'__VIEWSTATEGENERATOR': parse.quote(vsg, safe=""),
				'__EVENTVALIDATION': parse.quote(ev, safe=""),
				'ctl00$ContentPlaceHolder1$tsearch': parse.quote(f'{word}', safe="")
			}
			data = '&'.join([f"{key}={val}" for key, val in data.items()]) + '&'
			result = session.post(
				'https://lcorp.ulif.org.ua/dictua/dictua.aspx', 
				headers={
					'Content-Type': 'application/x-www-form-urlencoded',
					'Origin': 'https://lcorp.ulif.org.ua',
					'Referer': 'https://lcorp.ulif.org.ua/dictua/dictua.aspx'
				},
				data=data
			)
			result = BeautifulSoup(result.text, features='lxml')
			inflections = result.find('td', id='ctl00_ContentPlaceHolder1_article')
			if inflections:
				found_word = None
				word_info = None
				found_word = inflections.find(class_='word_style')
				if found_word:
					found_word = found_word.text.strip()
				word_info = inflections.find(class_='gram_style')
				if word_info:
					word_info = word_info.text.strip()
				rows = []
				for tr in inflections.find_all('tr'):
					row = []
					for td in tr.find_all('td'):
						row.append(td.text.strip())
					rows.append(row)
				ft = None
				if len(rows) == 0: 
					f = {}
				if len(rows) == 0:
					f = {}  # this is indeclinable
				elif rows[0][0] == 'Інфінітив':
					f = parse_verbs(rows)
					ft = 'verb'
				elif rows[1][0] == 'називний':
					f = parse_nouns(rows)
					ft = 'noun'
				elif rows[1][0] == 'чол. р.':
					f = parse_adjectives(rows)
					ft = 'adj'
				results.append([found_word, word_info, f, ft])
			else:  # this means it's a blank
				results.append([None, None, None, None])
	return results
			

def get_inflection(word, use_cache=True):
	
	translations = {
		'або': 'or',
		'абревіатура': 'abbreviations',
		'вигук': 'interjection',
		'виду': 'form',
		'вищий': 'highest',
		'власна': 'own',
		'вставне': 'interjection',
		'два': 'two',
		'доконаного': 'perfective',
		'дієприкметник': 'adjective',
		'дієприслівник': 'adverb',
		'дієслово': 'verb',
		'жіночого': 'female',
		'з': 'with',
		'займенник': 'pronoun',
		'кількісний': 'determiner',
		'множинний': 'plural',
		'назва': 'noun',
		'найвищий': 'lowest',
		'недоконаного': 'imperfective',
		'порядковий': 'adjective',
		'прийменник': 'preposition',
		'прийменником': 'preposition',
		'прикметник': 'adjective',
		'прислівник': 'adverb',
		'прислівником': 'adverb',
		'присудкове': 'predicate',
		'прізвище': 'noun',
		'роду': 'gender',
		'середнього': 'neuter',
		'слово': 'word',
		'сполука': 'conjunction',
		'сполучник': 'conjunction',
		'ступінь': 'degree',
		'типу': 'type',
		'частка': 'particle',
		'часткою': 'particle',
		'числівник': 'numeral',
		'чоловічого': 'male',
		'і': 'and',
		'іменник': 'noun',
		'істота': 'animate',
	}

	no_accent = word.get_word_no_accent()
	if no_accent not in inflection_cache or not use_cache:
		results = scrape_inflection(no_accent)
		inflection_cache[no_accent] = results
	else:
		results = inflection_cache[no_accent]

	def clean_result(res):
		found_word, word_info, forms, form_type = res
		if found_word:
			word_len = len(no_accent.split())
			found_word = ' '.join(found_word.split()[:word_len])
			forms = deepcopy(forms)
			word_info = ''.join([x for x in word_info if x in cyrillic + "' "])
			word_info = ' '.join([Word.replace_pos(translations[x]) for x in word_info.split()])
			
			for form_id in list(forms.keys()):
				form = forms[form_id]
				if form == "":
					del forms[form_id]
			for form_id in forms:
				form = forms[form_id]
				forms[form_id] = [x.strip() for x in form.split(',')]
				forms[form_id] = [' '.join(x.split()[-1 * word_len:]) for x in forms[form_id]]
			return (found_word, word_info, forms, form_type)
		return res

	results = [clean_result(x) for x in results]
	return results


def dump_inflection_cache():
	with open(f'data/inflection_raw_data.json', 'w+', encoding='utf-8') as f:
		f.write(json.dumps(inflection_cache, ensure_ascii=False, indent=2))


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
			'скорочення': 'abbreviation',
			'дієприсл.': 'participle'
		}
		data = defaultdict(lambda: {})
		with session.get('http://ukrkniga.org.ua/ukr_rate/publicist_84k_lex_dict_orig.csv', stream=True) as f:
			f.encoding = 'utf-8'
			rows = [row.split(';')[0:3] for row in f.text.split('\n')[1:-1]]
		for x in rows:
			data[
				x[1]  # word
			][
				parts_of_speech[x[2]]  # part of speech
			] = int(x[0])  # rank
		with open(f'data/frequencies.json', 'w+', encoding='utf-8') as f:
			f.write(json.dumps(data, indent=2, ensure_ascii=False))
	return data