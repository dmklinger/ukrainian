'use strict';

var main = (data, increase) => {
	let tr = d3.select(".main")
		.selectAll('.row')
		.data(data, (d) => { return d.index })
		.join('div')
	tr.attr('class', 'row')

	let gf = (o, form) => { if (form in o) { return o[form] }; return ['—']; }  // get form

	let single_noun_table = (obj, d) => {
		const word_data = [
			['Nom.', gf(d, 'nom n')],
			['Acc.', gf(d, 'acc n')],
			['Gen.', gf(d, 'gen n')],
			['Dat.', gf(d, 'dat n')],
			['Ins.', gf(d, 'ins n')],
			['Loc.', gf(d, 'loc n')],
			['Voc.', gf(d, 'voc n')],
		]
		const table = obj.append('table')
		for (let i=0; i < word_data.length; i++) {
			const row = word_data[i]
			const this_row = table.append('tr')
			this_row.append('th')
				.attr('id', 'leftLabel')
				.text(row[0])
			this_row.append('td')
				.selectAll('p')
				.data(row[1])
				.join('p')
				.text((d) => { return d })	
		}
	}

	let noun_table = (obj, d) => {
		const word_data = [
			['Nom.', gf(d, 'nom ns'), gf(d, 'nom np')],
			['Acc.', gf(d, 'acc ns'), gf(d, 'acc np')],
			['Gen.', gf(d, 'gen ns'), gf(d, 'gen np')],
			['Dat.', gf(d, 'dat ns'), gf(d, 'dat np')],
			['Ins.', gf(d, 'ins ns'), gf(d, 'ins np')],
			['Loc.', gf(d, 'loc ns'), gf(d, 'loc np')],
			['Voc.', gf(d, 'voc ns'), gf(d, 'voc np')],
		]
		const table = obj.append('table')
		const header_row = table.append('tr')  // header row
		header_row.append('th')
			.attr('id', 'leftLabel')
		header_row.append('th')
			.text('Sing.')
		header_row.append('th')
			.text('Plur.')
		for (let i=0; i < word_data.length; i++) {
			const row = word_data[i]
			const this_row = table.append('tr')
			this_row.append('th')
				.attr('id', 'leftLabel')
				.text(row[0])
			this_row.selectAll('td')
				.data(row.slice(1))
				.join('td')
				.selectAll('p')
				.data((d) => { return d })
				.join('p')
				.text((d) => { return d })	
		};
	}

	let adjective_table = (obj, d) => {
		const word_data = [
			['Nom.', gf(d, 'nom am'), gf(d, 'nom an'), gf(d, 'nom af'), gf(d, 'nom ap')],
			['Anim. Acc.', gf(d, 'gen am'), gf(d, 'nom an'), gf(d, 'acc af'), gf(d, 'gen ap')],
			['Inan. Acc.', gf(d, 'nom am'), gf(d, 'nom an'), gf(d, 'acc af'), gf(d, 'nom ap')],
			['Gen.', gf(d, 'gen am'), gf(d, 'gen an'), gf(d, 'gen af'), gf(d, 'gen ap')],
			['Dat.', gf(d, 'dat am'), gf(d, 'dat an'), gf(d, 'dat af'), gf(d, 'dat ap')],
			['Ins.', gf(d, 'ins am'), gf(d, 'ins an'), gf(d, 'ins af'), gf(d, 'ins ap')],
			['Loc.', gf(d, 'loc am'), gf(d, 'loc an'), gf(d, 'loc af'), gf(d, 'loc ap')],
		]

		const table = obj.append('table')
		const header_row = table.append('tr')  // header row
		header_row.append('th')
			.attr('id', 'leftLabel')
		header_row.append('th')
			.text('Male')
		header_row.append('th')
			.text('Neut.')
		header_row.append('th')
			.text('Fem.')
		header_row.append('th')
			.text('Plur.')
		for (let i=0; i < word_data.length; i++) {
			const row = word_data[i]
			const this_row = table.append('tr')
			this_row.append('th')
				.attr('id', 'leftLabel')
				.text(row[0])
			this_row.selectAll('td')
				.data(row.slice(1))
				.join('td')
				.selectAll('p')
				.data((d) => { return d })
				.join('p')
				.text((d) => { return d })	
		};
	}

	let verb_table = (obj, d) => {
		/* obj.append('p').text(JSON.stringify(d)) */
		let tenses = []
		for (const tense of ['past', 'pres', 'fut', 'imp']) {
			if (tense in d) { tenses.push(tense)}
		}
		const table = obj.append('table')
		const inf_tr = table.append('tr')
		inf_tr.append('th')
			.attr('id', 'leftLabel')
			.text('Inf.')
		inf_tr.append('td')
			.attr('colspan', 6)
			.selectAll()
			.data(gf(d, 'inf'))
			.join('p')
			.text((d) => { return d });

		for (const tense of tenses) {
			const tense_label = {
				'past': 'Past',
				'pres': 'Pres.',
				'fut': 'Fut.',
				'imp': 'Imp.'
			}[tense]
			const tense_categories = 
				(tense === 'past') 
				? ['m', 'n', 'f']
				: (tense === 'imp')
				? ['1', '2']
				: ['1', '2', '3']
			const tense_label_width = tense === 'imp' ? 3 : 2
			const tense_label_tr = table.append('tr')
			tense_label_tr.append('th')
				.attr('id', 'tenseMarker')
				.text(tense_label)
			tense_label_tr.selectAll()
				.data(tense_categories)
				.join('th')
				.attr('colspan', tense_label_width)
				.attr('id', 'tenseHeader')
				.text((d) => { 
					return {
						'm': 'Male',
						'n': 'Neuter',
						'f': 'Fem.',
						'1': '1st',
						'2': '2nd',
						'3': '3rd'
					}[d]
				})
			for (const number of ['s', 'p']) {
				const number_label_tr = table.append('tr')
				const number_label = number === 's' ? 'Sing.' : 'Plur.'
				number_label_tr.append('th')
					.attr('id', 'leftLabel')
					.text(number_label)
				if (tense === 'past' && number === 'p') {
					number_label_tr.append('td')
						.attr('colspan', 6)
						.selectAll()
						.data(gf(d['past'], 'p'))
						.join('p')
						.text((d) => { return d; })
				}
				else {
					number_label_tr.selectAll()
						.data(tense_categories)
						.join('td')
						.attr('colspan', tense_label_width)
						.selectAll()
						.data((tc) => {
							const form = `${tc}${number}`
							return gf(d[tense], form)
						})
						.join('p')
						.text((d) => { return d; })
				}
						
			}

			if ('pp' in d[tense]) {
				/* Active, passive, adverbial, impersonal */

				let pps = []
				for (const pp of ['act', 'pas', 'adv', 'imp']) {
					if (pp in d[tense]['pp']) { pps.push(pp) }
				}
				
				for (const pp of pps) {
					const participle_tr = table.append('tr')
					participle_tr.append('th')
						.attr('id', 'leftLabel')
						.text({
							'act': 'Act. Part.',
							'pas': 'Pass. Part.',
							'adv': 'Adv. Part.',
							'imp': 'Imp. Part.'
						}[pp])
					participle_tr.append('td')
						.attr('colspan', 6)
						.attr('id', 'ppLabel')
						.selectAll()
						.data(gf(d[tense]['pp'], pp))
						.join('p')
						.text((d) => { return d; })
				}
			}

		}
	}
	const div = tr.selectAll('div')
		.data((d) => { 
			return [
			d, d.forms
		]; })
		.enter()
			.append('div')
	div.attr('class', 'col')
	div.exit()
		.remove()
	div.each(function(d, i) {
			let this_obj = d3.select(this)
				.attr('id', 'def')
			if (i === 0) {
				this_obj.append('p')
					.attr('class', 'title')
					.append('b')
					.text(d.word)
				this_obj.append('p')
					.attr('class', 'title')
					.text(d.info ? ` (${d.pos} - ${d.info})` : ` (${d.pos})`)
				this_obj.append('div')
					.append('ul')
					.selectAll()
					.data(d.defs)
					.join('li')
					.text((d) => { return d;});
			} else if (i === 1) {
				this_obj.attr('id', 'forms')
				if ('nom n' in d || 'acc n' in d) {
					single_noun_table(this_obj, d)
				}
				else if ('nom ns' in d || 'nom np' in d) {
					noun_table(this_obj, d)
				}
				else if ('nom am' in d || 'nom af' in d || 'nom an' in d || 'nom ap' in d) {
					adjective_table(this_obj, d)
				}
				else if ('inf' in d) {
					verb_table(this_obj, d)
				}
				else if (Object.keys(d).length > 0) { 
					this_obj.text(JSON.stringify(d)) 
				}
				else {
					this_obj.append('p')
						.attr('id', 'indcl')
						.append('i')
						.text('indeclinable')
						
				}
			}
		});
	if (!increase) { window.scrollTo({top:0}); }
}

let numDisplayed = 300
let data;
let freq_data;
let alpha_data;
let curFilter;
let sortInfo = 'freq';
let index;
let searchTerm;

document.addEventListener('copy', (event) => {
	if (!document.querySelector('#stressCopy').checked) {
		const selection = document.getSelection()
		event.clipboardData.setData('text/plain', selection.toString().replaceAll('\u0301', ''))
		event.preventDefault()
	}
})

fetch('index.json')
	.then(res => res.json() )
	.then(out => { index = out; })
	.catch(err => {throw err; });

fetch('words.json')
	.then(res => res.json())
	.then(out => {
		data = out;
		freq_data = data;
		main(data.slice(0, numDisplayed))
		alpha_data = d3.sort(
			[...data], 
			x => x.word.toLowerCase()
				.replaceAll('\u0301', '')
				.split('')
				.map((y) => {
					const letters = Object({
						'а': '0',
						'б': '1',
						'в': '2',
						'г': '3',
						'ґ': '4',
						'д': '5',
						'е': '6',
						'є': '7',
						'ж': '8',
						'з': '9',
						'и': ':',
						'і': ';',
						'ї': '<',
						'й': '?',
						'к': '@',
						'л': 'A',
						'м': 'B',
						'н': 'C',
						'о': 'D',
						'п': 'E',
						'р': 'F',
						'с': 'G',
						'т': 'H',
						'у': 'I',
						'ф': 'K',
						'х': 'L',
						'ц': 'M',
						'ч': 'N',
						'ш': 'O',
						'щ': 'P',
						'ь': 'Q',
						'ю': 'R',
						'я': 'S',
						"'": 'T'
					})
					if (y in letters) return letters[y]
					return ''
				})
				.join()
		)
	})
	.catch(err => {throw err});

window.onscroll = (_) => {
	if (window.innerHeight + window.scrollY + 1000 >= document.body.offsetHeight) {
		numDisplayed += 100
		main(data.slice(0, numDisplayed), true);
	}
}

document.querySelector('input#search').addEventListener("keydown", event => {
	if (event.code === "Enter") { search(); };
})

window.addEventListener("keydown", event => {
    if (event.code === 'F3' || (event.ctrlKey && event.code === 'KeyF')) { 
        event.preventDefault();
		document.querySelector('input#search').focus();
    }
	if (event.code === 'Escape') {
		document.querySelector('input#search').value = ""
		search();
	}
})

function selectHelper() {
	if (sortInfo === 'freq') { data = freq_data }; 
	if (sortInfo === 'alpha') { data = alpha_data }; 
	if (sortInfo === 'alpha_rev') { data = d3.reverse(alpha_data) };
	numDisplayed = 300;
}

function filterHelper() {
	if (curFilter) {
		data = d3.filter(data, x => x.pos === curFilter);
		numDisplayed = 100;
	}
}

function searchHelper() {
	if (index && searchTerm) {
		searchTerm = searchTerm.trim().replaceAll(/\s+/g, ' ')
		// const literalResults = searchTerm.matchAll('"([^"]*)"')
		const literalResults = searchTerm.matchAll(/"([^"]*)"/g)
		let literalWords = Array()
		for (let literalRes of literalResults) {
			literalWords = literalWords.concat(literalRes[1].split(' '));
		}
		const fuzzyResults = searchTerm.replaceAll(/"([^"]*)"/g, '').trim().replaceAll(/\s+/g, ' ')
		let fuzzyWords = Array()
		for (let fuzzyRes of fuzzyResults.split(' ')) {
			fuzzyWords.push(fuzzyRes);
		}
		let indexes;
		for (let word of fuzzyWords) {
			if (!word) break;
			if (!indexes) {
				let results = d3.filter(Object.keys(index[word[0]]), x => x.startsWith(word) || x === word);
				indexes = []
				for (const res of results) { indexes = indexes.concat(index[res[0]][res])}
			} else {
				let results = d3.filter(Object.keys(index[word[0]]), x => x.startsWith(word) || x === word);
				let theseIndexes = []
				for (const res of results) { theseIndexes = theseIndexes.concat(index[res[0]][res])}
				indexes = d3.filter(indexes, x => theseIndexes.includes(x))
			}
		}
		for (let word of literalWords) {
			if (!word) break;
			if (!indexes) {
				let results = d3.filter(Object.keys(index[word[0]]), x => x === word);
				indexes = []
				for (const res of results) { indexes = indexes.concat(index[res[0]][res])}
				console.log(indexes)
			} else {
				let results = d3.filter(Object.keys(index[word[0]]), x => x === word);
				let theseIndexes = []
				for (const res of results) { theseIndexes = theseIndexes.concat(index[res[0]][res])}
				console.log(theseIndexes)
				indexes = d3.filter(indexes, x => theseIndexes.includes(x))
				console.log(indexes)
			}
		}
		if (indexes) {
			numDisplayed = 300;
			data = d3.filter(data, x => indexes.includes(x.index))
		}
	}
}
function select() {
	sortInfo = document.querySelector('select#sort').value;
	selectHelper();
	filterHelper();
	search();
	main(data.slice(0, numDisplayed));
}

function filter() {
	curFilter = document.querySelector('select#filter').value;
	selectHelper();
	filterHelper();
	search();
	main(data.slice(0, numDisplayed));
}

function search() {
	const oldSearch = searchTerm;
	searchTerm = document.querySelector('input#search').value.toLowerCase();
	if (oldSearch) {
		selectHelper();
		filterHelper();
	}
	searchHelper();
	main(data.slice(0, numDisplayed))
}