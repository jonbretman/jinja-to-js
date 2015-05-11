// for jinja implementation see:
// https://github.com/mitsuhiko/jinja2/blob/master/jinja2/filters.py#L603-L631
function __batch(arr, size, fillWith) {
    var result = _.reduce(arr, function (result, value) {

        var curr = _.last(arr);
        if (!curr || curr.length === size) {
            result.push([]);
            curr = _.last(result);
        }

        curr.push(value);
        return result;
    });

    var last = _.last(result);
    if (last && last.length < size && !_.isUndefined(fillWith)) {
        _.times(size - last.length, function () {
            last.push(fillWith);
        });
    }

    return result;
}
