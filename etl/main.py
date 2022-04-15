from ontolex import Ontolex

o = Ontolex(use_cache=True, use_raw_cache=True)
d = o.get_dictionary()
d.add_wiktionary_words()
d.dump('dictionary_data.json', indent=4, final_form=True)
d.make_index('index.json', 'word_dict.json', indent=4)
d.dump('../../words.json', final_form=True)
d.make_index('../../index.json', '../../word_dict.json')
