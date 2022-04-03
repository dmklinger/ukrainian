'use strict';

var main = (data) => {
	let data_sliced = data.slice(0, 300)
	let tr = d3.select("body")
		.append('div')
			.attr('class', 'main')
			.selectAll()
		.data(data_sliced)
		.join('div')
			.attr('class', 'row')

	let gf = (o, form) => { if (form in o) { return o[form] }; return ['—']; }  // get form

	let single_noun_table = (obj, d) => {
		let word_data = [
			[['nom.'], ['acc.'], ['gen.'], ['dat.'], ['ins.'], ['loc.'], ['voc.']],
			[gf(d, 'nom n'), gf(d, 'acc n'), gf(d, 'gen n'), gf(d, 'dat n'), gf(d, 'ins n'), gf(d, 'loc n'), gf(d, 'voc n')]
		]
		obj.append('table')
			.selectAll()
			.data(word_data)
			.join('tr')
			.each(function(d, i) {
				let itemTag = i === 0 ? 'th' : 'td';
				d3.select(this)
					.selectAll()
					.data((d) => { return d })
					.join(itemTag).selectAll()
					.data((d) => { return d })
					.join('p')
					.text((d) => { return d })	
			})	
	}

	let noun_table = (obj, d) => {
		let word_data = [
			[['nom.'], ['acc.'], ['gen.'], ['dat.'], ['ins.'], ['loc.'], ['voc.']],
			[gf(d, 'nom ns'), gf(d, 'acc ns'), gf(d, 'gen ns'), gf(d, 'dat ns'), gf(d, 'ins ns'), gf(d, 'loc ns'), gf(d, 'voc ns')],
			[gf(d, 'nom np'), gf(d, 'acc np'), gf(d, 'gen np'), gf(d, 'dat np'), gf(d, 'ins np'), gf(d, 'loc np'), gf(d, 'voc np')]
		]
		let table = obj.append('table')
		table.selectAll()
			.data(word_data)
			.join('tr')
			.each(function(d, i) {
				let itemTag = i === 0 ? 'th' : 'td';
				let numberLabel = '';
				if (i === 1) { numberLabel = 'Sing.'}
				if (i === 2) { numberLabel = 'Plur.'}
				let t = d3.select(this)
				t.append('th')
						.attr('id', 'leftLabel')
						.text(numberLabel)
				t.selectAll()
					.data((d) => { return d })
					.join(itemTag).selectAll()
					.data((d) => { return d })
					.join('p')
					.text((d) => { return d });
			})
			
	}

	let adjective_table = (obj, d) => {
		let word_data = [
			[['nom.'], ['acc.', '(anim.)'], ['acc.', '(inan.)'], ['gen.'], ['dat.'], ['ins.'], ['loc.']],
			[gf(d, 'nom am'), gf(d, 'gen am'), gf(d, 'nom am'), gf(d, 'gen am'), gf(d, 'dat am'), gf(d, 'ins am'), gf(d, 'loc am')],
			[gf(d, 'nom an'), gf(d, 'nom an'), gf(d, 'nom an'), gf(d, 'gen an'), gf(d, 'dat an'), gf(d, 'ins an'), gf(d, 'loc an')],
			[gf(d, 'nom af'), gf(d, 'acc af'), gf(d, 'acc af'), gf(d, 'gen af'), gf(d, 'dat af'), gf(d, 'ins af'), gf(d, 'loc af')],
			[gf(d, 'nom ap'), gf(d, 'gen ap'), gf(d, 'nom ap'), gf(d, 'gen ap'), gf(d, 'dat ap'), gf(d, 'ins ap'), gf(d, 'loc ap')]
		]
		let table = obj.append('table')
		table.selectAll()
			.data(word_data)
			.join('tr')
			.each(function(d, i) {
				let itemTag = i === 0 ? 'th' : 'td';
				let numberLabel = '';
				if (i === 1) { numberLabel = 'Male'}
				if (i === 2) { numberLabel = 'Neut.'}
				if (i === 3) { numberLabel = 'Fem.'}
				if (i === 4) { numberLabel = 'Plur.'}
				let t = d3.select(this)
				t.append('th')
						.attr('id', 'leftLabel')
						.text(numberLabel)
				t.selectAll()
					.data((d) => { return d })
					.join(itemTag).selectAll()
					.data((d) => { return d })
					.join('p')
					.text((d) => { return d });
			})
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
			const tenses_tr = table.append('tr')
			tenses_tr.append('th')
				.attr('id', 'leftLabel')  // no left label
			tenses_tr.append('th')
				.attr('colspan', 6)
				.attr('id', 'tenseLabel')
				.text(tense_label)
			const tense_categories = 
				(tense === 'past') 
				? ['m', 'n', 'f']
				: (tense === 'imp')
				? ['1', '2']
				: ['1', '2', '3']
			const tense_label_width = tense === 'imp' ? 3 : 2
			const tense_label_tr = table.append('tr')
			tense_label_tr.append('th')
				.attr('id', 'leftLabel')  // no left label
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
				number_label_tr.selectAll()
					.data(tense_categories)
					.join('td')
					.attr('colspan', tense_label_width)
					.selectAll()
					.data((tc) => {
						const form = (number === 'p' && tense === 'past') ? 'p' : `${tc}${number}`
						console.log(form)
						return gf(d[tense], form)
					})
					.join('p')
					.text((d) => { return d; })
						
			}
		}
	}

	tr.selectAll()
		.data((d) => { return [d.info ? [d.pos, `(${d.info})`] : [d.pos], d.word, d.freq, d.defs, d.forms]; })
			.enter()
		.append('div')
			.attr('class', 'col')
		.each(function(d, i) {
			let this_obj = d3.select(this)
			switch (i) {
				case 0: {
					this_obj.selectAll()
						.data(d)
						.join('p')
						.text((d) => { return d; });
					break;
				}
				case 3: {
					this_obj.attr('id', 'def')
						.append('ul')
						.selectAll()
						.data(d)
						.join('li')
						.text((d) => { return d;});
					break;
				}
				case 4: {
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
					break;
				}
				default: this_obj.append('p').text(d);
			}
		});
}

fetch('words.json')
	.then(res => res.json())
	.then(out => { main(out); })
	.catch(err => {throw err});