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
	tr.selectAll()
		.data((d) => { return [d['pos'], d['word'], d['freq'], d['defs'], d['forms']]; })
		.join('td')
		.text((d) => { return JSON.stringify(d); });
}

fetch('/words.json')
	.then(res => res.json())
	.then(out => { console.log(out); main(out); })
	.catch(err => {throw err});