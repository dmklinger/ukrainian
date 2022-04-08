from ontolex import Ontolex
import extract

o = Ontolex(use_cache=True, use_raw_cache=True)
d = o.get_dictionary()
d.add_wiktionary_words()
d.dump('dictionary_data.json', indent=4)
