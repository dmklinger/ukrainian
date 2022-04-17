import json
import re
from copy import deepcopy
from collections import defaultdict

import extract

cyrillic = "ЄІЇАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдежзийклмнопрстуфхцчшщъыьэюяєії"

class Forms:
	
	def __init__(self, forms, form_type):
		self.forms = {}
		self.add_forms(forms)
		self.form_type = form_type
		
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

		# remove duplicates
		for form_id in self.forms:
			form_list = self.forms[form_id]
			new_form_list = {form.replace('*', ''): None for form in form_list}
			self.forms[form_id] = [x for x in new_form_list]

		# remove unaccented forms when an accented form exists
		for form_id in self.forms:
			form_list = self.forms[form_id]
			base_forms = defaultdict(lambda: 0)
			for f in form_list:
				base_forms[f.replace("́", "")] = max(base_forms[f.replace("́", "")], f.count("́")) 
			new_form_list = []
			for f in form_list:
				if f.count("́") == base_forms[f.replace("́", "")]:
					new_form_list.append(f)
			self.forms[form_id] = new_form_list

	def get_final_forms(self):
		if self.form_type != 'verb':
			return self.forms
		else:
			new_forms = defaultdict(lambda: defaultdict(lambda: {}))
			for form in [x for x in self.forms if x != 'inf']:
				info = form.split(' ')
				if len(info) == 2:
					new_forms[info[0]][info[1]] = self.forms[form]
				elif len(info) == 3:
					new_forms[info[0]]['pp'][info[1]] = self.forms[form]
			new_forms['inf'] = self.forms['inf']
			for form in new_forms:
				if isinstance(new_forms[form], defaultdict):
					new_forms[form] = dict(new_forms[form])
			return new_forms


class Usage:

	def __init__(self, word, pos):
		self.word = word
		self.pos = pos
		self.definitions = {}
		self.alerted_definitions = {}
		self.frequency = None
		self.forms = {}
		self.info = {}
		self.delete_me = False

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
		gender, aspect, animacy = set(), set(), set()
		for info in self.info:
			for word in info.split():
				if word in ('f', 'female'):
					gender.add('female')
				if word in ('m', 'male'):
					gender.add('male')
				if word in ('animal', 'animate'):
					animacy.add('animate')
				if word in ('n', 'neuter'):
					gender.add('neuter')
				if word in ('inan'):
					animacy.add('inanimate')
				if word in ('imperfective', 'impf'):
					aspect.add('imperfective')
				if word in ('pf', 'perfective'):
					aspect.add('perfective')
		new_info = []
		if len(gender) > 0:
			gender = ' or '.join(gender)
			new_info.append(gender)
		if len(aspect) > 0:
			aspect = ' or '.join(aspect)
			new_info.append(aspect)
		if len(animacy) > 0:
			animacy = ' or '.join(animacy)
			new_info.append(animacy)
		if len(new_info) > 0:
			new_info = ", ".join(new_info)
		else:
			new_info = ""
		return new_info

	def add_forms(self, forms, form_type):
		if form_type in self.forms:
			self.forms[form_type].add_forms(forms)
		else:
			forms = Forms(forms, form_type)
			self.forms[form_type] = forms

	def add_inflection(self, results, force=False):

		def get_inflection_positions(word):
			word = word + '|'  # end of word marker, irrelevant
			word_split = [(word[i], word[i+1]) for i in range(len(word) - 1) if word[i] != "́"]
			result = set([i for i in range(len(word_split)) if word_split[i][1] == "́"])
			return result

		added_flag = False
		new_usages = []
		self.delete_me = True
		for found_word, word_info, forms, form_type in results:
			if found_word and self.pos and self.pos in word_info:  
				if self.word == found_word: # perfect match!
					self.add_info(word_info)
					self.add_forms(forms, form_type)
					added_flag = True
					self.delete_me = False
				else:
					this_inflection = get_inflection_positions(self.word) 
					found_inflection = get_inflection_positions(found_word)
					if len([x for x in this_inflection if x not in found_inflection]) == 0:  # stress could be elsewhere
						new_usage = Usage(found_word, self.pos)
						new_usage.definitions = deepcopy(self.definitions)
						new_usage.alerted_definitions = deepcopy(self.alerted_definitions)
						new_usage.add_info(word_info)
						new_usage.add_forms(forms, form_type)
						new_usages.append(new_usage)
						added_flag = True

			elif force:
				if self.word == found_word:
					if self.pos in ('noun', 'verb', 'adjective') and self.pos != form_type:
						new_usage = Usage(self.word, form_type)
						new_usage.definitions = deepcopy(self.definitions)
						new_usage.alerted_definitions = deepcopy(self.alerted_definitions)
						new_usage.add_info(word_info)
						new_usage.add_forms(forms, form_type)
						new_usages.append(new_usage)
					else:
						self.add_info(word_info)
						self.add_forms(forms, form_type)
						self.delete_me = False
		if force and self.pos not in ('noun', 'verb', 'adjective'):
			self.delete_me = False
		if not added_flag and len(self.forms) > 0:
			self.delete_me = False
		return not added_flag and len(self.forms) == 0, new_usages

	def get_definitions(self, accept_alerts=True):
		result = []
		for d, pov in self.definitions.items():
			if pov and pov not in d:
				d = f"{d} ({pov})"
			if accept_alerts or d not in self.alerted_definitions:
				result.append(d)
		return result

	def get_forms(self, final_forms=False):
		results = {}
		for form_id in self.forms:
			forms = self.forms[form_id].forms
			if final_forms:
				forms = self.forms[form_id].get_final_forms()
			results = {**results, **forms}
		return results

	def get_definition_words(self):
		results = []
		for d in self.get_definitions():
			d = d.replace('́', '')
			new_d = ''
			parenthesis = 0
			for l in d:
				if l == '(':
					parenthesis += 1
				elif l == ')':
					parenthesis -= 1
				elif parenthesis == 0:
					new_d += l
			d = new_d 
			d = re.sub(r"[^A-Za-z']+", ' ', d).strip().split()
			results += d
		return results

	def get_form_words(self):
		results = []
		for forms in self.get_forms().values():
			for f in forms:
				f = f.replace('́', '')
				f = re.sub(r"[^\w']+", ' ', f).strip().split()
				results += f
		return results

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
		for ft, forms in other.forms.items():
			if ft in self.forms:
				self.forms[ft].add_forms(forms.forms)
			else:
				self.forms[ft] = forms
		if len(self.info) == 0 and len(other.info) > 0:
			self.info = other.info

	def get_dict(self, final_forms=False):
		return {
			'defs': self.get_definitions(),
			'freq': self.frequency,
			'info': self.get_info(),
			'forms': self.get_forms(final_forms)
		}


class Word:


	def __init__(self, word):
		if word == "будова (bud'''o'''wa)":
			word = 'будова'
		self.word = word
		self.usages = {}

	def replace_pos(pos):
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
			return replace[pos]
		return pos

	def get_word_no_accent(self):
		return self.word.replace("́", "")

	def add_definition(self, pos, definition):
		if pos == 'verb' and len(definition.split()) == 1:
			definition = f"to {definition}"
		if '[1]' in definition:
			definition = definition.replace('[1]', '')
		elif definition.endswith(']') and '[' not in definition:
			definition = definition[:-1]
		bad_stuff = [
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
			(',)', ')'),
			(',,', ','),
			(', (', ' ('),
			('!slash!', '/')
		]
		for x, y in bad_stuff:
			if x in definition:
				definition = definition.replace(x, y)
		definition = ' '.join(definition.split())
		if 'This term needs a translation to English. Please help out and add a translation, then remove the text' in definition:
			return  # No
		if 'This term needs a translation to English. Please help out and add a translation, then remove the text rfdef.' in definition:
			return # No

		replaced = pos

		pos = Word.replace_pos(pos)
		if pos == replaced:
			replaced = None

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
			if len(usage.definitions.keys()) == 0 or usage.delete_me or pos in ('suffix', 'prefix'):
				if(len(usage.definitions.keys()) == 0):
					print(f'DELETING: {self.word}, {pos} - reason: no more definitions')
				elif usage.delete_me:
					print(f'DELETING: {self.word}, {pos} - reason: said to delete')
				elif pos in ('suffix', 'prefix'):
					print(f'DELETING: {self.word}, {pos} - reason: bad pos')
				del self.usages[pos]

	def add_frequencies(self, frequencies):
		if frequencies:
			for pos in list(frequencies.keys()):
				frequencies[Word.replace_pos(pos)] = frequencies[pos]
		for pos, usage in self.usages.items():
			if frequencies:
				if pos in frequencies:
					usage.add_frequency(frequencies[pos])
				else:
					usage.add_frequency(None)
			else:
				usage.add_frequency(None)

	def add_info(self, pos, word_info):
		if pos in self.usages:
			self.usages[pos].add_info(word_info)
		
	def add_forms(self, pos, forms, form_type):
		self.usages[pos].add_forms(forms, form_type)

	def add_inflections(self, results):
		needs_flag = True
		new_usages = []
		for usage in self.usages.values():
			this_needs, nu = usage.add_inflection(results)
			if not this_needs:
				needs_flag = False
			new_usages += nu
		if needs_flag:
			for usage in self.usages.values():
				_, nu = usage.add_inflection(results, force=True)
				new_usages += nu
		return new_usages

	def get_final_form(self):
		results = []
		for pos, usage in self.usages.items():
			result = {'word': self.word, 'pos': pos}
			result = {**result, **usage.get_dict(final_forms=True)}
			results.append(result)
		return results

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
				print(f'DELETING WORD: {w}')
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
				if i % 1000 == 0:
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

	def get_final_forms(self):
		result = []
		for word in self.dict:
			result += self.dict[word].get_final_form()

		max_freq = max([x['freq'] if x['freq'] else -1 for x in result])
		result = sorted(
			result, 
			key=lambda x: (
				x['freq'] if x['freq'] is not None else max_freq + 1, 
				len(x['word']), 
				x['word']
			)
		)
		for i, r in enumerate(result):
			r['index'] = i
		return result

	def make_index(self, loc1, loc2, indent=None):
		data = self.get_final_forms()
		word_index = defaultdict(lambda: set())
		for i, d in enumerate(data):
			word = self.dict[d['word']]
			usage = word.usages[d['pos']]
			def_words = usage.get_definition_words()
			form_words = usage.get_form_words() + [word.get_word_no_accent()]
			for d in def_words:
				d = d.lower()
				word_index[d].add(i)
			for f in form_words:
				f = f.lower()
				word_index[f].add(i)

		word_index_list = {}
		word_part = defaultdict(lambda: set())
		for i, word in enumerate(list(word_index.keys())):
			word_index_list[i] = [word, list(word_index[word])]
			for l in word:
				word_part[l].add(i)
		for i in word_part:
			word_part[i] = list(word_part[i])

		with open(f'data/{loc1}', 'w+', encoding='utf-8') as f:
			if indent:
				f.write(
					json.dumps(word_index_list, indent=indent, ensure_ascii=False)
				)
			else:
				f.write(
					json.dumps(word_index_list, ensure_ascii=False)
				)

		with open(f'data/{loc2}', 'w+', encoding='utf-8') as f:
			if indent:
				f.write(
					json.dumps(word_part, indent=indent, ensure_ascii=False)
				)
			else:
				f.write(
					json.dumps(word_part, ensure_ascii=False)
				)

	def dump(self, loc, indent=None, final_form=False):
		if final_form:
			data = self.get_final_forms()
		else:
			data = self.get_dict()

		with open(f'data/{loc}', 'w+', encoding='utf-8') as f:
			if indent:
				f.write(
					json.dumps(data, indent=indent, ensure_ascii=False)
				)
			else:
				f.write(
					json.dumps(data, ensure_ascii=False)
				)