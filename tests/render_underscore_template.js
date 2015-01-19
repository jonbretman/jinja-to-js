var _ = require('underscore');
var fs = require('fs');

var args = process.argv;
var templates = {};
var data = JSON.parse(readFile(args[args.length - 1]));
var mainTemplate, i, parts;

for (i = 2; i < args.length - 1; i++) {
    parts = parseTemplateArgument(args[i]);
    templates[parts.name] = _.template(readFile(parts.path), {variable: 'context'});

    if (i == 2) {
        mainTemplate = parts.name;
    }
}

data.include = function (name) {
    return templates[name];
};

process.stdout.write(templates[mainTemplate](data));

function readFile(name) {
    return fs.readFileSync(name, 'utf8');
}

function parseTemplateArgument(str) {
    var parts = str.split(':');
    return {
        name: parts[0],
        path: parts[1]
    }
}
