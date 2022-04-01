'use strict';

var main = (data) => {
	let data_sliced = data.slice(0, 300)
	let tr = d3.select("body")
		.append('table')
		.append('tbody').selectAll()
		.data(data_sliced)
		.join('tr')

	tr.selectAll()
		.data((d) => { return [d.info ? [d.pos, `(${d.info})`] : [d.pos], d.word, d.freq, d.defs, d.forms]; })
		.enter()
		.append('td')
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
					if (Object.keys(d).length > 0) { 
						this_obj.text(JSON.stringify(d)) 
					};
					break;
				}
				default: this_obj.text(d);
			}
		});
}

fetch('words.json')
	.then(res => res.json())
	.then(out => { main(out); })
	.catch(err => {throw err});