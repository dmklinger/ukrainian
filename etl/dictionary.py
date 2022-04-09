import json
from copy import deepcopy
from collections import defaultdict

import extract

cyrillic = "ЄІЇАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдежзийклмнопрстуфхцчшщъыьэюяєії"

class Forms:
	
	def __init__(self, forms, form_type):
		self.forms = forms
		self.form_type = form_type


class Usage:

	def __init__(self, word, pos):
		self.word = word
		self.pos = pos
		self.definitions = {}
		self.alerted_definitions = {}
		self.frequency = None
		self.forms = {}
		self.info = {}
		self.could_not_find_forms = False

	def add_definitions(self, definitions):
		for d in definitions:
			self.add_definition(d)

	def add_definition(self, definition, replaced=None, alert=False):
		if alert:
			self.alerted_definitions[definition] = replaced
		self.definitions[definition] = replaced
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
				'verbal',
				'acronym',
				'equivalent',
				'abbreviation',
				'dialectical',
				'('
			]
			if sum([1 if af in d.lower() else 0 for af in acceptable_forms]) > 0:
				matched_word = None
				if found_word in dictionary.dict:
					matched_word = dictionary.dict[found_word]
				elif found_word.replace("́", '') in dictionary.dict:
					matched_word = dictionary.dict[found_word.replace("́", '')]
				if matched_word:
					if self.pos in matched_word.usages:
						self.merge(matched_word.usages[self.pos], accept_alerts=False)
					self.add_definition(d)
				elif len(self.definitions.keys()) == len(self.alerted_definitions.keys()):
					del self.definitions[d]
					del self.alerted_definitions[d]
			else:
				del self.definitions[d]
				del self.alerted_definitions[d]
	
	def add_frequency(self, frequency):
		self.frequency = frequency

	def add_info(self, info):
		if info:
			self.info[info] = None

	def get_info(self):
		return list(self.info.keys())

	def add_forms(self, forms):
		if forms: 
			if self.forms:
				for key in (self.forms.keys() | forms.keys()):
					these_forms = []
					other_forms = []
					if key in self.forms:
						these_forms = self.forms[key]
					if key in forms:
						other_forms = forms[key]
					surplus = []
					if len(these_forms) < len(other_forms):
						surplus = other_forms[len(these_forms):]
					elif len(these_forms) > len(other_forms):
						surplus = these_forms[len(other_forms):]
					self.forms[key] = [x for pair in zip(these_forms, other_forms) for x in pair] + surplus
			else:
				self.forms = forms

	def add_inflection(self, results, force=False):

		def get_inflection_positions(word):
			word = word + '|'  # end of word marker, irrelevant
			word_split = [(word[i], word[i+1]) for i in range(len(word) - 1) if word[i] != "́"]
			result = set([i for i in range(len(word_split)) if word_split[i][1] == "́"])
			return result

		added_flag = False
		new_usages = []
		for found_word, word_info, forms in results:
			if found_word and self.pos and self.pos in word_info:  
				if self.word == found_word: # perfect match!
					self.add_info(word_info)
					self.add_forms(forms)
					added_flag = True
				else:
					this_inflection = get_inflection_positions(self.word) 
					found_inflection = get_inflection_positions(found_word)
					if len([x for x in this_inflection if x not in found_inflection]) == 0:  # stress could be elsewhere
						new_usage = Usage(found_word, self.pos)
						new_usage.definitions = deepcopy(self.definitions)
						new_usage.alerted_definitions = deepcopy(self.alerted_definitions)
						new_usage.add_info(word_info)
						new_usage.add_forms(forms)
						new_usages.append(new_usage)
						added_flag = True
			elif force:
				if self.word == found_word:
					self.add_info(word_info)
					self.add_forms(forms)
		if not added_flag:
			print(self.word)
			print(self.pos)
			print(results)
			print('--------------------')
		return added_flag, new_usages

	def get_definitions(self, accept_alerts=True):
		result = []
		for d, pov in self.definitions.items():
			if pov and pov not in d:
				d = f"{d} ({pov})"
			if accept_alerts or d not in self.alerted_definitions:
				result.append(d)
		return result

	def merge(self, other, accept_alerts=True):
		new_usage = Usage(self.word, self.pos)
		these_definitions = self.get_definitions()
		other_definitions = other.get_definitions()
		min_length = min(len(these_definitions), len(other_definitions))
		for pair in zip(self.get_definitions(), other.get_definitions(accept_alerts)):
			new_usage.add_definition(pair[0], alert=pair[0] in self.alerted_definitions)
			new_usage.add_definition(pair[1], alert=pair[1] in other.alerted_definitions)
		if len(these_definitions) > len(other_definitions):
			for d in these_definitions[(len(these_definitions) - min_length):]:
				new_usage.add_definition(d, alert=d in self.alerted_definitions)
		elif len(other_definitions) > len(these_definitions):
			for d in other_definitions[(len(other_definitions) - min_length):]:
				new_usage.add_definition(d, alert=d in other.alerted_definitions)
		self.definitions = new_usage.definitions
		self.alerted_definitions = new_usage.alerted_definitions
		if len(self.forms.keys()) == 0 and len(other.forms.keys()) > 0:
			self.forms = other.forms

	def get_dict(self):
		return {
			'defs': self.get_definitions(),
			'freq': self.frequency,
			'info': self.get_info(),
			'forms': self.forms
		}


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
		if pos == 'verb' and len(definition.split()) == 1:
			definition = f"to {definition}"
		if '[1]' in definition:
			definition = definition.replace('[1]', '')
		elif definition.endswith(']') and '[' not in definition:
			definition = definition[:-1]
		for x, y in [
				('“', '"'), 
				('”', '"'), 
				(r'{{', ''), 
				(r'}}', ''), 
				('()', ''), 
				('\u200b', ''), 
				(' :', ':'), 
				('’', "'"),
				(',:', ':'),
				('\\', ''),
				(',)', ')')
			]:
			if x in definition:
				definition = definition.replace(x, y)
		definition = ' '.join(definition.split())
		if 'This term needs a translation to English. Please help out and add a translation, then remove the text' in definition:
			return  # No
		if 'This term needs a translation to English. Please help out and add a translation, then remove the text rfdef.' in definition:
			return # No

		replaced = None

		if pos in replace:
			replaced = pos
			pos = replace[pos]

		if pos in self.usages:
			u = self.usages[pos]
		else:
			u = Usage(self.word, pos)
			self.usages[pos] = u
		if ' of ' in definition and definition.split(' of ')[1][0] in cyrillic:
			if ':' in definition or ';' in definition:
				u.add_definition(definition, replaced=replaced, alert=False)
			else:
				u.add_definition(definition, replaced=replaced, alert=True)
		else:
			u.add_definition(definition, replaced=replaced, alert=False)

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

	def add_frequencies(self, frequencies):
		for pos, usage in self.usages.items():
			if frequencies:
				if pos in frequencies:
					usage.add_frequency(frequencies[pos])
				else:
					usage.add_frequency(None)
			else:
				usage.add_frequency(None)

	def add_info(self, pos, word_info):
		self.usages[pos].add_info(word_info)
		
	def add_forms(self, pos, forms):
		self.usages[pos].add_forms(forms)

	def add_inflections(self, results):
		added_flag = False
		new_usages = []
		for usage in self.usages.values():
			added_flag, nu = usage.add_inflection(results)
			new_usages += nu
		return new_usages

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
		print('parsing wiktionary data')
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
		print('done parsing wiktionary data')
		self.clean_alerted_words()
		self.garbage_collect()
		self.add_frequencies()
		self.get_inflections()
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

	def add_frequencies(self):
		frequencies = extract.get_frequency_list()
		for _, word in self.dict.items():
			if word.get_word_no_accent() in frequencies:
				word.add_frequencies(frequencies[word.get_word_no_accent()])
			else:
				word.add_frequencies(None)

	def get_inflections(self):
		print("getting inflections")
		try:
			n = len(self.dict.values())
			for i, word in enumerate(list(self.dict.keys())):
				if i % 100 == 0:
					print(f"{i} of {n}")
				w = self.dict[word]
				results = extract.get_inflection(w)
				new_usages = w.add_inflections(results)
				for n_u in new_usages:
					new_w = Word(n_u.word)
					new_w.usages[n_u.pos] = n_u
					self.add_to_dictionary(new_w)
		except Exception as e:
			raise e
		finally:
			extract.dump_inflection_cache()

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