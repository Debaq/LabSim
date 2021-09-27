const input_list = ["Aérea", "Ósea", "LDL", "Campo_libre"];
const side_list = ["OD", "OI"];
const mkg_list = { Aérea: ["c/mkg", "s/mkg"], Ósea: ["c/mkg", "s/mkg"], LDL: [""], Campo_libre:["s/mkg"] };
const freq_list = ["125", "250", "500", "1k", "2k", "3k", "6k", "8k", "12k"];

function tables(name) {
    let table = document.createElement("table");
    table.id = name;
    let caption = document.createElement("caption");
    caption.innerText = name;
    caption.id = name + "_caption";
    let thead = document.createElement("thead");
    thead.id = name + "_head";
    let tbody = document.createElement("tbody");
    tbody.id = name + "_body";
    table.appendChild(caption);
    table.appendChild(thead);
    table.appendChild(tbody);
    return table;
}

function frecuency(freq, side, mkg) {
    var data = [...freq];
    data.unshift(side);
    let row = document.createElement("tr");
    for (let i in data) {
        let row_data = document.createElement("td");
        if (i == 0) {
            let label_side = document.createElement("text");
            label_side.innerHTML = side + " " + mkg;
            row_data.appendChild(label_side);
        } else {
            let input_db = document.createElement("input");
            input_db.type = "number";
            input_db.min = -15;
            input_db.max = 120;
            input_db.step = 5;
            input_db.value = 20;
            input_db.size = 3;
            input_db.name = data[i] + "_" + side;
            input_db.id = data[i] + "_" + side;

            row_data.appendChild(input_db);
        }
        row.appendChild(row_data);
    }

    return row;
}

function heading(name) {
    var data = [...name];
    data.unshift("Lado/Frec.");
    let row = document.createElement("tr");
    for (let i in data) {
        let head = document.createElement("th");
        head.innerHTML = data[i];
        row.appendChild(head);
    }
    return row;
}

function create_tables(name) {
    var head_str = name + "_head";
    var body_str = name + "_body";

    tab = tables(name);
    document.getElementById("body").appendChild(tab);
    head = heading(freq_list);
    document.getElementById(head_str).appendChild(head);

    for (let j in side_list) {
        for (let k in mkg_list[name]) {
            body = frecuency(freq_list, side_list[j], mkg_list[name][k]);
            document.getElementById(body_str).appendChild(body);
        }
    }
}

for (i in input_list) {
    create_tables(input_list[i]);
}


function create_json(){

    var ids = document.querySelectorAll('[id]');

    Array.prototype.forEach.call( ids, function( el, i ) {
        // "el" is your element
        console.log( el.id ); // log the ID
    });

    return el.id;
}
