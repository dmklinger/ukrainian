'use strict';

var main = (data) => {
	data.sort((a, b) => { 
		a = a['freq'];
		b = b['freq'];
		return (a === null) - ( b===null ) || -(b > a) || +(b < a);
	})
	console.log(data)
	let data_sliced = data.slice(0, 5000)
	let tr = d3.select("body")
		.append('table')
		.append('tbody').selectAll()
		.data(data_sliced)
		.join('tr')

	tr.selectAll('td')
		.data((d) => { return [d.pos, d.word, d.freq, d.defs, d.forms]; })
		.enter()
		.append('td')
		.each(function(d, i) {
			let this_obj = d3.select(this)
			switch (i) {
				case 3: {
					this_obj.selectAll()
						.data(d)
						.join('ul')
						.text((d) => {console.log(d); return d;});
					break;
				}
				case 4: {
					this_obj.text(JSON.stringify(d))
					break;
				}
				default: this_obj.text(d);
			}
		});
}

fetch('words.json')
	.then(res => res.json())
	.then(out => { console.log(out); main(out); })
	.catch(err => {throw err});