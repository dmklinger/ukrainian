import json
from collections import defaultdict

import extract

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

	def get_dict(self):
		return self.get_definitions()


class Word:

	def __init__(self, word):
		if word == "будова (bud'''o'''wa)":
			word = 'будова'
		self.word = word
		self.usages = {}

	def get_word_no_accent(self):
		return self.word.replace("́", "")

	def add_definition(self, pos, definition):
		replace = {
			'conjunction': 'particle',
			'determiner': 'particle',
			'interjection': 'particle',
			'letter': 'noun',
			'number': 'numeral',
			'numeral': 'numeral',
			'postposition': 'particle',
			'predicative': 'particle',
			'preposition': 'particle',
			'prepositional phrase': 'phrase',
			'proper noun': 'noun',
		}
		if pos in replace:
			if pos not in definition:
				definition = f"{definition} ({pos})"
			pos = replace[pos]
		if pos in self.usages:
			u = self.usages[pos]
		else:
			u = Usage(self.word, pos)
			self.usages[pos] = u
		u.add_definition(definition)

	def merge(self, other):
		for pos, usage in other.usages.items():
			if pos in self.usages:
				self.usages[pos].merge(usage)
			else:
				self.usages[pos] = usage

	def get_dict(self):
		dict = {}
		for k, v in self.usages.items():
			dict[k] = v.get_dict()
		return dict


class Dictionary:

	def __init__(self):
		self.dict = {}
		self.accentless_words = defaultdict(lambda: set())

	def _handle_no_accent(self, to_add, no_accent):
		if no_accent == to_add.word:
			# very easy, we just merge this in with the other one
			self.dict[
				list(self.accentless_words[no_accent])[0]
			].merge(to_add)
		else:
			added_flag = False
			for e in list(self.accentless_words[no_accent]):
				existant_word = self.dict[e]
				existant_word_no_accent = existant_word.get_word_no_accent()
				if existant_word_no_accent == e and not added_flag:
					to_add.merge(existant_word)
					self.dict.pop(e)
					self.accentless_words[no_accent].remove(e)
					if len(self.accentless_words[no_accent]) == 0:
						self.accentless_words.pop(no_accent)
					self.dict[to_add.word] = to_add	
					added_flag = True
			if not added_flag:  # they are different words
				self.dict[to_add.word] = to_add

	def _add_word_to_dictionary(self, to_add):
		if to_add.word in self.dict:
			self.dict[to_add.word].merge(to_add)
		else:
			no_accent = to_add.get_word_no_accent()
			if no_accent in self.accentless_words:
				self._handle_no_accent(to_add, no_accent)
			else:
				self.dict[to_add.word] = to_add		
				self.accentless_words[no_accent].add(to_add.word)

	def add_to_dictionary(self, to_add):
		if isinstance(to_add, Word):
			self._add_word_to_dictionary(to_add)
		if isinstance(to_add, list):
			for w in to_add:
				self._add_word_to_dictionary(w)

	def add_wiktionary_words(self):
		print("adding wiktionary words")
		print('extracting lemmas')
		words = extract.get_lemmas()
		print('done extracting lemmas')
		n = len(words)
		try:
			for i, w in enumerate(words):
				if i % 100 == 0:
					print(f"{i // 100} of {n // 100}")
				result = extract.get_wiktionary_word(w)
				for r in result:
					self.add_to_dictionary(r)
		finally:
			extract.dump_wiktionary_cache()


	def get_dict(self):
		dict = {}
		for k, v in self.dict.items():
			dict[k] = v.get_dict()
		return dict

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