from dictionary import Ontolex

o = Ontolex(read='ontolex_data.json')
o.dump('ontolex_data.json', indent=2)
d = o.get_dictionary()
print(d)