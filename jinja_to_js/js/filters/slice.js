// for jinja implementation see:
// https://github.com/mitsuhiko/jinja2/blob/master/jinja2/filters.py#L567-L600
function __slice(value, slices, fillWith) {
    var hasFillWith = !_.isUndefined(fillWith) && !_.isNull(fillWith);
    var length = value.length;
    var itemsPerSlice = Math.floor(length / slices);
    var slicesWithExtra = length % slices;
    var offset = 0;
    var result = [];

    _.times(slices, function (slice_number) {
        var start = offset + slice_number * itemsPerSlice;

        if (slice_number < slicesWithExtra) {
            offset += 1;
        }

        var end = offset + (slice_number + 1) * itemsPerSlice;
        var tmp = value.slice(start, end);

        if (hasFillWith && slice_number >= slicesWithExtra) {
            tmp.append(fillWith);
        }

        result.push(tmp);
    });

    return result;
}
