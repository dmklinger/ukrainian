import extract
from dictionary import Word, Dictionary
import json

class Ontolex_Word:

	def __init__(self, word, data=None):
		self.word = word
		if data:
			self.data = data
		else:
			self.data = {}

	def add_gloss(self, gloss, part_of_speech, can_exist=False):
		definition, translation = None, []
		part_of_speech = part_of_speech.lower() if part_of_speech is not None else None
		if gloss in self.data:
			definition, translation = self.data[gloss]['def'], self.data[gloss]['translation']
		if can_exist or gloss not in self.data:
			self.data[gloss] = {
				'pos': part_of_speech,
				'def': definition,
				'translation': translation
			}

	def add_translation(self, gloss, translation):
		if translation.endswith(' f') or translation.endswith(' m'):
			translation = translation.replace(' f', '(female form)')
			translation = translation.replace(' m', '(male form)')
		self.data[gloss]['translation'].append(translation)
	
	def add_definition(self, gloss, definition):
		self.data[gloss]['def'] = definition

	def get_translations(self):
		results = []
		for _, gloss_data in self.data.items():
			pos, definition, translations = gloss_data['pos'], gloss_data['def'], gloss_data['translation']
			for t in translations:
				if t in results:
					w = results[t]
				else:
					w = Word(t)
				if not definition:
					definition = self.word
				if self.word not in definition:
					w.add_definition(pos, self.word)
				else:
					w.add_definition(pos, definition)
				results.append(w)
		return results

	def get_dict(self):
		return self.data
			

class Ontolex:

	def __init__(self, use_cache=True, use_raw_cache=True):	
		self.words = {}	
		if use_cache:
			try:
				with open(f"data/ontolex_data.json", 'r', encoding='utf-8') as f:
					data = json.loads(f.read())
				for w, o_w in data.items():
					self.words[w] = Ontolex_Word(w, o_w)
				return
			except:
				pass
		extract.get_ontolex(use_cache=use_raw_cache)
		self.parse_ontolex()
		self.dump('ontolex_data.json')

	def get_word(self, word):
		if word not in self.words:
			self.words[word] = Ontolex_Word(word)
		return self.words[word]

	def parse_ontolex(self):
		print('parsing ontolex data')
		with open('data/raw_dbnary_dump.ttl', 'r', encoding='utf-8-sig') as f:
			data = f.read().split('\n')
		n = len(data)
		divisor = 10 ** 6
		for i, line in enumerate(data):
			if i % divisor == 0:
				print(f"{i // divisor} of {n // divisor}")
			if 'eng:__en_gloss' in line:
				gloss = line.split(';')[0].split('>')[0].split('/')[-1].split('.')[0].split(':')[-1].strip()
				vals = [x.replace('_', ' ').strip() for x in '_'.join(gloss.split('_')[5:]).split('__')]
				word = vals[0]
				new_word = word
				part_of_speech = vals[1] if len(vals) > 1 else None
				self.get_word(word).add_gloss(gloss, part_of_speech)
			if 'dbnary:isTranslationOf' in line:
				translation = line.split(';')[0].split('>')[0].split('/')[-1].split('.')[0].split(':')[-1].strip().replace('__en_gloss', '')
				vals = [x.replace('_', ' ').strip() for x in translation.split('__')]
				new_word = vals[0]
				if new_word == word:
					part_of_speech = vals[1] if len(vals) > 1 else None
					self.get_word(word).add_gloss(gloss, part_of_speech)
			if '@uk' in line:
				translation = line.split('@')[0].replace('\\\"', '*').split("\"")[1].replace('*', '\\\"').replace('[','').replace(']','')
				translation = " ".join([x.split('|')[0] for x in translation.split(' ')])
				if new_word == word:
					self.get_word(word).add_translation(gloss, translation)
			if 'rdf:value' in line and "@en" in line and '[' not in line:
				definition = line.split('@')[0].replace('\\\"', '*').split("\"")[1].replace('*', '\\\"')
				if new_word == word:
					self.get_word(word).add_definition(gloss, definition)
		print('parsing complete')

	
	def get_dictionary(self):
		dict = Dictionary()
		for _, word in self.words.items():
			translations = word.get_translations()
			dict.add_to_dictionary(translations)
		return dict

	def get_dict(self):
		d = {}
		for w in self.words:
			d[w] = self.words[w].get_dict()
		return d

	def dump(self, loc, indent=None):
		with open(f'data/{loc}', 'w+', encoding='utf-8') as f:
			if indent:
				f.write(
					json.dumps(self.get_dict(), indent=indent, ensure_ascii=False)
				)
			else:
				f.write(
					json.dumps(self.get_dict(), ensure_ascii=False)
				)
