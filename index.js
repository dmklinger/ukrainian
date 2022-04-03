'use strict';

var main = (data) => {
	console.log(data)
	let tr = d3.select(".main")
		.selectAll('.row')
		.data(data, (d) => { return JSON.stringify([d.word, d.pos]) })
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
				else if ('nom am' in d) {
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
}

let numDisplayed = 300
let data;
let freq_data;
let alpha_data;

document.addEventListener('copy', (event) => {
	if (!document.querySelector('#stressCopy').checked) {
		const selection = document.getSelection()
		event.clipboardData.setData('text/plain', selection.toString().replaceAll('\u0301', ''))
		event.preventDefault()
	}
})

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
		main(data.slice(0, numDisplayed));
	}
}

function select() {
	const sort_info = document.querySelector('select').value
	if (sort_info === 'freq') { data = freq_data }; 
	if (sort_info === 'alpha') { data = alpha_data }; 
	if (sort_info === 'alpha_rev') { data = d3.reverse(alpha_data) };
	numDisplayed = 300;
	main(data.slice(0, numDisplayed))
}
