var fs = require('fs');

var args = process.argv;
var templates = {};

var dataFileName = args[args.length - 1];
var dataFileText = readFile(dataFileName);

try {
    var data = JSON.parse(dataFileText);
} catch (e) {
    throw new Error('Unable to parse data ' + dataFileText + ' from file ' + dataFileName);
}

for (var key in data) {
    if (data[key] === '<<< MAKE ME A FUNCTION >>>') {
        data[key] = function () { return 'hello'; };
    }
}

// add custom filter
require('../jinja-to-js-runtime.js').filters.unicode_snowmen = function (value) {
    return value.split('').map(function () {
        return '☃';
    }).join('');
};

// add custom global
require('../jinja-to-js-runtime.js').globals.convert_to_uppercase = function (val) {
    return val.toUpperCase();
};

process.stdout.write(require(args[2])(data));

function readFile(name) {
    try {
        return fs.readFileSync(name, 'utf8');
    } catch (e) {
        throw new Error('Unable to read file ' + name);
    }
}
