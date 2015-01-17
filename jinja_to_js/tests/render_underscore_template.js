var _ = require('underscore');
var fs = require('fs');

var templateFilePath = process.argv[2];
var jsonFilePath = process.argv[3];

var template = fs.readFileSync(templateFilePath, 'utf8');
var data = JSON.parse(fs.readFileSync(jsonFilePath, 'utf8'));

process.stdout.write(
    _.template(template, {variable: 'context'})(data)
);
