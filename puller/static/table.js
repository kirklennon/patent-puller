var queryString = window.location.search;

function generateTable(table, patents, patentsFoundParagraphFullText) {

	for (let element of patents) {
		let tr = document.createElement('tr');  
		let td1 = document.createElement('td');
		let td2 = document.createElement('td');
		let td3 = document.createElement('td');
		let td4 = document.createElement('td');
		let td5 = document.createElement('td');
		
		let patent_no = document.createTextNode(element['number']);
		let patent_title = document.createTextNode(element['title']);
		let abstract = document.createTextNode(element['abstract']);
		let inventors = document.createTextNode(element['inventors']);
		let assignee = document.createTextNode(element['assignee']);
		
		td1.appendChild(patent_no);
		td2.appendChild(patent_title);
		td3.appendChild(abstract);
		td4.appendChild(inventors);
		td5.appendChild(assignee);
		
		tr.appendChild(td1);
		tr.appendChild(td2);
		tr.appendChild(td3);
		tr.appendChild(td4);
		tr.appendChild(td5);
  
	  table.appendChild(tr);
	}
	
	patentsFoundParagraph.innerText = patentsFoundParagraphFullText;
	
}
 
let table = document.querySelector("tbody");
let patentsFoundParagraph = document.querySelector("#patentsFoundParagraph");

function searchPatents(){
	patentNumberList = document.getElementById('rawPatentInput').value;
	getData();
}

function generateQueryString() {
	return `?countPerPage=${countPerPage}&sort=${sort}&selectedClass=${selectedClass}&selectedQuality=${selectedQuality}&priceMin=${priceMin}&priceMax=${priceMax}&caratMin=${caratMin}&caratMax=${caratMax}&selectedLocation=${selectedLocation}&serialSearch=${serialSearch}`
}

async function getData(data = {'patentNumberList': patentNumberList}) {
	table.innerHTML = '';
	fetch('/search', {
		method: "POST",
		cache: "no-cache", 
		headers: {
			  "Content-Type": "application/json",
			},
		body: JSON.stringify(data)
	})
	  .then(function (response) {
		return response.json();
	  })
	  .then(function (searchResults) {
		patentsFoundParagraphFullText = `“Perkins Coie” was found in assignment information for the following patents: ${searchResults.firmNameFoundList}`
		patents = searchResults.patentDictList;
		// firmNameFoundIn = searchResults.firmNameFoundList;
		
		generateTable(table, patents, patentsFoundParagraphFullText);
	  })
	  .catch(function (err) {
		console.log(err);
	  });
}