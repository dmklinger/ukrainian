from ontolex import Ontolex

o = Ontolex(use_cache=False)
d = o.get_dictionary()
d.add_wiktionary_words()
d.dump('dictionary_data.json', indent=4)
