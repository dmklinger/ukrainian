import extract
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
			translation = translation[:-3]
		self.data[gloss]['translation'].append(translation)
	
	def add_definition(self, gloss, definition):
		self.data[gloss]['def'] = definition

	def get_translations(self):
		results = []
		for _, gloss_data in self.data.items():
			pos, definition, translations = gloss_data['pos'], gloss_data['def'], gloss_data['translation']
			for t in translations:
				if not definition:
					definition = self.word
				if self.word not in definition:
					definition = f"{self.word}, {definition}"
				if t in results:
					w = results[t]
				else:
					w = Word(t)
				w.add_definition(pos, definition)
				results.append(w)
		return results

	def get_dict(self):
		return self.data
			

class Ontolex:

	def __init__(self, get_data=False, read=None):
		if get_data:
			extract.get_ontolex()
		self.words = {}
		if read:
			with open(f"data/{read}", 'r', encoding='utf-8') as f:
				data = json.loads(f.read())
			for w, o_w in data.items():
				self.words[w] = Ontolex_Word(w, o_w)
		else:
			self.parse_ontolex()

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


class Usage:

	def __init__(self, word, pos):
		self.word = word
		self.pos = pos
		self.definitions = {}

	def add_definitions(self, definitions):
		for d in definitions:
			self.add_definition(d)

	def add_definition(self, definition):
		self.definitions[definition] = None

	def get_definitions(self):
		return list(self.definitions)

	def merge(self, other):
		self.add_definitions(
			[item for pair in zip(self.get_definitions(), other.get_definitions()) for item in pair]
		)


class Word:

	def __init__(self, word):
		self.word = word
		self.usages = {}

	def get_word_no_accent(self):
		return self.word.replace("́", '')

	def add_definition(self, pos, definition):
		if pos in self.usages:
			u = self.usages[pos]
		else:
			u = Usage(self.word, pos)
			self.usages[pos] = u
		u.add_definition(definition)

	def merge(self, other):
		for pos, usage in other:
			if pos in self.usages:
				self.usages[pos].merge(usage)
			else:
				self.usages[pos] = usage


class Dictionary:

	def __init__(self):
		self.dict = {}

	def add_to_dictionary(self, to_add):
		if isinstance(to_add, Word):
			if to_add.word in self.dict:
				self.dict[to_add.word].merge(to_add)
			else:
				self.dict[to_add.word] = to_add
		if isinstance(to_add, list):
			for w in to_add:
				self.add_to_dictionary(w)

	def to_dict(self):
		dict = {}
		for k, v in self.dict:
			dict[k] = v.to_dict()
