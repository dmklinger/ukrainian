'use strict';

var main = (data) => {
	let data_sliced = data.slice(0, 1000)
	let tr = d3.select("body")
		.append('div')
			.attr('class', 'main')
			.selectAll()
		.data(data_sliced)
		.join('div')
			.attr('class', 'row')

	let gf = (o, form) => { if (form in o) { return o[form] }; return ['[no form]']; }  // get form

	let single_noun_table = (obj, d) => {
		// obj.text(JSON.stringify(d))
		let word_data = [
			[['nom.'], ['acc.'], ['gen.'], ['dat.'], ['ins.'], ['loc.'], ['voc.']],
			[gf(d, 'nom n'), gf(d, 'acc n'), gf(d, 'gen n'), gf(d, 'dat n'), gf(d, 'ins n'), gf(d, 'loc n'), gf(d, 'voc n')]
		]
		obj.append('table').selectAll()
			.data(word_data)
			.join('tr').selectAll()
			.data((d) => { return d })
			.join('td').selectAll()
			.data((d) => { return d })
			.join('p')
			.text((d) => { return d })
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
					this_obj
						.append('ul')
						.attr('id', 'def')
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
						this_obj.append('p')
							.text('noun s/p form')
					}
					else if ('nom am' in d) {
						this_obj.append('p')
							.text('adj form')
					}
					else if ('inf' in d) {
						this_obj.append('p')
							.text('verb form')
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