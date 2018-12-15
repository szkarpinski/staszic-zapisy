
function match(query, value) {

    function simplify(string) {return string.toLowerCase().replace(/ą/g, 'a').replace(/ć/g, 'c').replace(/ę/g, 'e')
        .replace(/ł/g, 'l').replace(/ń/g, 'n').replace(/ó/g, 'o').replace(/ś/g, 's').replace(/ż/g, 'z').replace(/ź/g, 'z')};
    query = simplify(query); value = simplify(value);
    return query.split(" ").every(function(word) {return value.indexOf(word)>=0;});
}

function search(query, set, empty) {
    var filtered = []; for (t of set) if (match(query, t.name)) filtered.push(t);
    filtered = filtered.sort(function (a, b) {return a.lname.localeCompare(b.lname)});
    mapped = []; for (f of filtered) mapped.push(f.rendered);
    return (filtered.length > 0 ? mapped.join('') : empty);
}