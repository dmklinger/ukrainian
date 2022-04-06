from dictionary import Ontolex

o = Ontolex(read='ontolex_data.json')
d = o.get_dictionary()
d.dump('dictionary_data.json', indent=4)