/*
 * RankingEntry
 */

// Constructor
function RankingEntry(eventNr, points) {
	this.eventNr = eventNr;
	this.points = points;
	this.counts = true;
}

/*
 * Runner
 */

// Constructor
function Runner(name, club) {
	this.name = name;
	this.club = club;
	this.rankingEntries = [];
	this.zeroValues = 0;
	this.total = 0;
}

Runner.prototype.addEntry = function (nr, points) {
	var entry; // The entry that's going to be added.
	
	if (typeof(points) != 'number') {
		points = parseInt(points, 10);
	}
	entry = new RankingEntry(nr, points);
	
	this.rankingEntries[nr] = entry;
	
	if (points === 0) {
		this.zeroValues +=1 ;
	}
};

Runner.prototype.getEntry = function (eventNr) {
	return this.rankingEntries[eventNr];
};

Runner.prototype.checkCounts = function () {
	var i; // Loop over the events that don't count;
	
	var year = document.getElementsByTagName('H1')[0].childNodes[0].childNodes[0].nodeValue;
	year = parseInt(year.substr(year.length-4, 4),10);
	
	var requiredEntries = 8;
	if (year < 2007) {
		requiredEntries = 5;
	} else if (year < 2018) {
		requiredEntries = 6;
	}
	
	if (this.rankingEntries.length > requiredEntries && this.zeroValues <= 2) {
		this.rankingEntries.sort(
			function (a, b) {
				return b.points - a.points;
			}
		);
		
		for (i = requiredEntries; i < this.rankingEntries.length; i++) {
			this.rankingEntries[i].counts = false;
		}
		
		this.rankingEntries.sort(
			function (a, b) {
				return a.eventNr - b.eventNr;
			}
		);
	}
};

Runner.prototype.getPoints = function (eventNr) {
	if (eventNr === -1) {
		return this.getTotal();
	} else {
		return this.rankingEntries[eventNr].points;
	}
};

Runner.prototype.getTotal = function () {
	return this.total;
};

Runner.prototype.setTotal = function (total) {
	if (typeof(total) != 'number') {
		total = parseInt(total, 10);
	}
	this.total = total;
};

Runner.prototype.toString = function () {
	return "" + this.name + " " + this.club;
};

/*
 * Ranking
 */

// Constructor
function Ranking() {
	this.table = null;
	this.runners = [];
	this.sortedOn = -1;
}

Ranking.createFromTable = function (table, contentStart) {
	var club,        // The clubname of a runner
	    i,           // Loop counter for table rows
	    j,           // Loop counter for cells in a row
	    name,        // The name of a runner
	    points,      // The points the runner scored in an event
	    ranking,     // Newly created Ranking object
	    runner,      // A Runner object
	    totalCell;   // Reference to the table cell with the total score of the runner

	ranking = new Ranking();
	ranking.table = table;
	
	for (i = 0; i < table.rows.length; i++) {
		name = table.rows[i].cells[1].childNodes[0].nodeValue;
		if (contentStart && (contentStart !== 2)) {
			club = table.rows[i].cells[2].childNodes[0].nodeValue;
		}
		
		runner = new Runner(name, club);
		
		for (j = contentStart; j < table.rows[i].cells.length - 1; j++) {
			points = table.rows[i].cells[j].childNodes[0].nodeValue;
			
			runner.addEntry(j - contentStart, points);
		}
		
		totalCell = table.rows[i].cells[table.rows[i].cells.length-1];
		runner.setTotal( parseInt(totalCell.childNodes[0].nodeValue, 10) );
		
		runner.checkCounts();
		
		ranking.runners.push(runner);
	}
	return ranking;
};

Ranking.prototype.rebuildTable = function () {
	var cell,    // The cell that's added.
	    entry,   // A RankingEntry object of the runner
	    frag,    // DocumentFragment: only reflow when table is inserted (except IE)
	    i,       // Loop counter for Runners
	    j,       // Loop counter for events
	    last,    // Remember the points of the last runner (for ex-aequo)
	    place,   // The place the runner currently has
	    row,     // The row in the table that corresponds to the runner
	    runner,  // The runner that's being processed
	    tbody,   // The table body that's rewritten
	    totCell; // The cell with the total score
	
	tbody = this.table.tBodies[0];
	if (!tbody) {
		return;
	}
	if (document.implementation.createDocument) {
		frag = document.createDocumentFragment();
		frag.appendChild(tbody);
	}
	
	// remove old elements
	while (tbody.firstChild) {
		tbody.removeChild(tbody.firstChild);
	}
	
	
	last=0;
	place =0;
	for (i = 0; i < this.runners.length; i++ ) {
		runner = this.runners[i];
		row = tbody.insertRow(-1);
		
		row.insertCell(-1).appendChild(document.createTextNode(runner.name));
		if (runner.club) {
			row.insertCell(-1).appendChild(document.createTextNode(runner.club));
		}
		
		for (j = 0; j < runner.rankingEntries.length; j++ ) {
			entry = runner.rankingEntries[j];
			
			cell = row.insertCell(-1);
			cell.appendChild( document.createTextNode(entry.points) );
			if (entry.counts === false && entry.points !== 0) {
				// cell.setAttribute("class","dropped"); Doesn't work in IE!!!
				cell.style.textDecoration = "line-through";
			}
		}
		
		totCell = row.insertCell(-1);
		totCell.className = "tot";
		totCell.appendChild(document.createTextNode(runner.getTotal()));
		
		if (last !== runner.getPoints(this.sortedOn) && runner.getPoints(this.sortedOn) !== 0 ){
			place = i + 1;
			last = runner.getPoints(this.sortedOn);
		} else {
			place = "";
		}
		row.insertCell(0).appendChild( document.createTextNode(place) );
	}
	
	if (frag) {
		this.table.appendChild(frag);
	}
};

Ranking.prototype.sort = function (nr) {
	var sortRows; // Function to sort an array of Runners
	
	sortRows = function (a, b) {
		if (nr === -1) {
			// total
			return b.getTotal() - a.getTotal();
		} else {
			var r = b.getPoints(nr) - a.getPoints(nr);
			if (r === 0){
				return b.getTotal() - a.getTotal();
			} else {
				return r;
			}
		}
	};
	
	this.runners.sort(sortRows);
	this.sortedOn = nr;
};

Ranking.prototype.makeInteractive = function () {
	var i,            // Loop over all events
	    messageCell,  // textNode where messages can be set.
	    row,          // The row to choose the event
	    self = this,  // Provide acces to this Ranking object from an inner function
	    th;           // A cell for the row

	row = this.table.createTHead().insertRow(-1);
	
	th = document.createElement("TH");
	th.colSpan = this.makeInteractive.thSpan||3; // Newer rankings have club in a separate col
	th.appendChild( document.createTextNode("Sort:") );
	messageCell = th.childNodes[0];
	
	row.appendChild(th);
	
	// Add the events
	for (i = 0; i < this.runners[0].rankingEntries.length; i++) {
		th = document.createElement("TH");
		th.appendChild( document.createTextNode("E" + (i+1)) );
		
		(function () {
			var nr = i;
			th.onclick = function () {
				self.sort(nr);
				self.rebuildTable();
				for (var j = 1; j < row.cells.length; j++){
					row.cells[j].className = "";
				}
				this.className = "sort";
			};
			th.onmouseover = function () {
				if (self.events) {
					messageCell.nodeValue = "Sort: "+self.events[nr];
				}
			};
			th.onmouseout = function () {
				if (self.events) {
					messageCell.nodeValue = "Sort:";
				}
			};
		})();
		
		row.appendChild(th);
	}
	
	// Allow sorting on total
	th = document.createElement("TH");
	th.appendChild( document.createTextNode("TOT") );
	th.onclick = function () {
		self.sort(-1);
		self.rebuildTable();
		for (var j = 1; j < row.cells.length; j++){
			row.cells[j].className = "";
		}
		this.className = "sort";
	};
	
	th.onmouseover = function () {
		if (self.events) {
			messageCell.nodeValue = "Sort: TOTAL";
		}
	};
	th.onmouseout = function () {
		if (self.events) {
			messageCell.nodeValue = "Sort:";
		}
	};
	row.appendChild(th);
};

Ranking.prototype.loadEventData = function (uri) {
	var i,            // Loop over all events
	    names,        // Collection of all eventnames
	    req,          // The XMLHttpRequest object to load the eventinfo file
	    self = this;  // Reference to this ranking object

	if (window.XMLHttpRequest){
        req = new XMLHttpRequest();
    } else if (window.ActiveXObject){
        req = new ActiveXObject("Microsoft.XMLHTTP");
    }
	
	if (req) {
		req.onreadystatechange = function () {
			if (req.readyState === 4 && (req.status === 200 || req.status === 304) ) {
				names = req.responseXML.getElementsByTagName("name");
				
				self.events = [];
				for (i = 0; i < names.length; i++){
					self.events[i] = names[i].childNodes[0].nodeValue;
				}
			}
		};
		req.open("GET", uri, true);
		req.send(null);
	}
};

window.onload = function () {
	var table = document.getElementsByTagName("TABLE")[0];
	if (table.rows.length === 0){
		return;
	}
	
	var jaar=document.getElementsByTagName('H1')[0].childNodes[0].childNodes[0].nodeValue;
	jaar=parseInt(jaar.substr(jaar.length-4, 4),10);
	
	if (jaar < 2006) {
		var natcrit = Ranking.createFromTable(table, 2);
	} else {
		var natcrit = Ranking.createFromTable(table, 3);
	}
	
	natcrit.loadEventData("../N"+jaar+".xml?nocache="+ new Date().getTime());
	
	if (jaar < 2006) {
		natcrit.makeInteractive.thSpan = 2;
	}
	natcrit.makeInteractive();
	
	natcrit.sort(-1);
	natcrit.rebuildTable();
};
