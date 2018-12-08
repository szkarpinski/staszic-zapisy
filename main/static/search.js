
function match(query, value) {

    function simplify(string) {return string.toLowerCase().replace(/ą/g, 'a').replace(/ć/g, 'c').replace(/ę/g, 'e')
        .replace(/ł/g, 'l').replace(/ń/g, 'n').replace(/ó/g, 'o').replace(/ś/g, 's').replace(/ż/g, 'z').replace(/ź/g, 'z')};

    query = simplify(query); value = simplify(value);
    return query.split(" ").every(function(word) {return value.includes(word);});
}

function search(query, set, empty) {
    let filtered = set.filter(t => match(query, t.name))
        .sort(function (a, b) {return a.lname.localeCompare(b.lname)});
    return (filtered.length > 0 ? filtered.map(f => f.rendered).join('') : empty);
}