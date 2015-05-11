function __title(s) {
    s = s + '';
    return s.split(' ').map(function (word) {
        return word[0].toUpperCase() + word.substring(1).toLowerCase();
    }).join(' ');
}
