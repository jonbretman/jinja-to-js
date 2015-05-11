# this function emulates Pythons boolean evaluation e.g. an empty list or object is false
PYTHON_BOOL_EVAL_FUNCTION = """
function __ok(o) {
    var toString = Object.prototype.toString;
    return !o ? false : toString.call(o).match(/\[object (Array|Object)\]/) ? !_.isEmpty(o) : !!o;
}
"""

CAPITALIZE_FUNCTION = """
function __capitalize(s) {
    return s ? s[0].toUpperCase() + s.substring(1) : s;
}
"""

BATCH_FUNCTION = """
function __batch(arr, size, fillWith) {
    var result = _.reduce(arr, function (result, value) {

        var curr = _.last(result);
        if (!curr || curr.length === size) {
            result.push([]);
            curr = _.last(result);
        }

        curr.push(value);
        return result;
    }, []);

    var last = _.last(result);
    if (last && last.length < size && !_.isUndefined(fillWith)) {
        _.times(size - last.length, function () {
            last.push(fillWith);
        });
    }

    return result;
}
"""

DEFAULT_FUNCTION = """
function __default(obj, defaultValue, boolean) {
    defaultValue = _.isUndefined(defaultValue) ? '' : defaultValue;
    boolean = _.isUndefined(boolean) ? false : boolean;

    var toString = Object.prototype.toString;
    var test;

    if (boolean === true) {
        test = !obj ? false :
                      toString.call(obj).match(/\[object (Array|Object)\]/) ? !_.isEmpty(obj) :
                                                                              !!obj;
    }
    else {
        test = !_.isUndefined(obj);
    }

    return test ? obj : defaultValue;
}
"""

INT_FUNCTION = """
function __int(value, defaultValue) {
    defaultValue = _.isUndefined(defaultValue) ? 0 : defaultValue;
    value = parseInt(value, 10);
    return isNaN(value) ? defaultValue : value;
}
"""

SLICE_FUNCTION = """
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
            tmp.push(fillWith);
        }

        result.push(tmp);
    });

    return result;
}
"""

TITLE_FUNCTION = """
function __title(s) {
    s = s + '';
    return s.split(' ').map(function (word) {
        return word[0].toUpperCase() + word.substring(1).toLowerCase();
    }).join(' ');
}
"""

TRUNCATE_FUNCTION = """
function __truncate(s, length, killwords, end) {
    s = s + '';
    length = _.isUndefined(length) ? 255 : length;
    killwords = _.isUndefined(killwords) ? false : killwords;
    end = _.isUndefined(end) ? '...' : end;

    var endLength = end.length;

    if (s.length <= length) {
        return s;
    }

    if (killwords) {
        return s.substring(0, length) + end;
    }

    var words = s.split(' ');
    var result = [];
    var m = 0, i = 0;

    for (; i < words.length; i++) {
        m += words[i].length + 1;

        if (m > length) {
            break;
        }

        result.push(words[i]);
    }
    result.push(end);
    return result.join(' ');
}
"""
