from ontolex import Ontolex

o = Ontolex(read='ontolex_data.json')
# o.dump('ontolex_data.json')
d = o.get_dictionary()
d.add_wiktionary_words()
d.dump('dictionary_data.json', indent=4)
