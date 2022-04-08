import json
from collections import defaultdict
import re

import extract

cyrillic = "ЄІЇАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдежзийклмнопрстуфхцчшщъыьэюяєії"


class Usage:

	def __init__(self, word, pos):
		self.word = word
		self.pos = pos
		self.definitions = {}
		self.alerted_definitions = {}

	def add_definitions(self, definitions):
		for d in definitions:
			self.add_definition(d)

	def add_definition(self, definition, alert=False):
		if alert:
			self.alerted_definitions[definition] = None
		self.definitions[definition] = None
		# check to ensure definitions are not redundant
		bad_defs = set()
		for d1 in self.definitions.keys():
			for d2 in self.definitions.keys():
				if d1 != d2 and d1.lower() in d2.lower():
					bad_defs.add(d1)
		for d in bad_defs:
			del self.definitions[d]
			if d in self.alerted_definitions:
				del self.alerted_definitions[d]

	def clean_alerted_words(self, dictionary):
		for d in list(self.alerted_definitions.keys()):
			initial_index = None
			found_word = ''
			for i, x in enumerate(d):
				if x in cyrillic + ' ' + "'" + "́":
					found_word = found_word + x
				if x in cyrillic + "'" + "́" and initial_index is None:
					initial_index = i
			found_word = found_word.strip()
			acceptable_forms = [
				'alternative', 
				'contraction', 
				'synonym', 
				'diminutive', 
				'initialism', 
				'endearing',
				'augmentative',
				'variant',
				'comparative',
			]
			if sum([1 if af in d.lower() else 0 for af in acceptable_forms]) > 0:
				matched_word = None
				if found_word in dictionary.dict:
					matched_word = dictionary.dict[found_word]
				elif found_word.replace("́", '') in dictionary.dict:
					matched_word = dictionary.dict[found_word.replace("́", '')]
				if matched_word:
					if self.pos in matched_word.usages:
						self.merge(matched_word.usages[self.pos])
					self.add_definition(d)
				elif len(self.definitions.keys()) == len(self.alerted_definitions.keys()):
					del self.definitions[d]
					del self.alerted_definitions[d]
			else:
				del self.definitions[d]
				del self.alerted_definitions[d]

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
		if pos == 'verb' and len(definition.split()) == 1:
			definition = f"to {definition}"
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
		if '[1]' in definition:
			definition = definition.replace('[1]', '')
		elif definition.endswith(']') and '[' not in definition:
			definition = definition[:-1]
		for x, y in [('“', '"'), ('”', '"'), (r'{{', ''), (r'}}', ''), ('()', ''), ('\u200b', ''), (' :', ':')]:
			if x in definition:
				definition = definition.replace(x, y)
		definition = ' '.join(definition.split())
		if 'This term needs a translation to English. Please help out and add a translation, then remove the text' in definition:
			return  # No
		if 'This term needs a translation to English. Please help out and add a translation, then remove the text rfdef.' in definition:
			return # No

		if pos in self.usages:
			u = self.usages[pos]
		else:
			u = Usage(self.word, pos)
			self.usages[pos] = u
		if ' of ' in definition and definition.split(' of ')[1][0] in cyrillic:
			if ':' in definition or ';' in definition:
				u.add_definition(definition, alert=False)
			else:
				u.add_definition(definition, alert=True)
		else:
			u.add_definition(definition, alert=False)

	def merge(self, other):
		for pos, usage in other.usages.items():
			if pos in self.usages:
				self.usages[pos].merge(usage)
			else:
				self.usages[pos] = usage

	def clean_alerted_words(self, dictionary):
		for _, usage in self.usages.items():
			usage.clean_alerted_words(dictionary)

	def garbage_collect(self):
		for pos in list(self.usages.keys()):
			usage = self.usages[pos]
			if len(usage.definitions.keys()) == 0:
				del self.usages[pos]

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
					print(f"{i} of {n}")
				result = extract.get_wiktionary_word(w)
				for r in result:
					self.add_to_dictionary(r)
		except Exception as e:
			raise e
		finally:
			extract.dump_wiktionary_cache()
		print('cleaning words that are defined in reference to another')
		self.clean_alerted_words()
		self.garbage_collect()

	def clean_alerted_words(self):
		for _, w in self.dict.items():
			w.clean_alerted_words(self)

	def garbage_collect(self):
		for w in list(self.dict.keys()):
			word = self.dict[w]
			word.garbage_collect()
			if len(word.usages.keys()) == 0:
				del self.dict[w]

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