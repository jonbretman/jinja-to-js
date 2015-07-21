# this function emulates Pythons boolean evaluation e.g. an empty list or object is false
PYTHON_BOOL_EVAL_FUNCTION = """
function __ok(o) {
    if (!o) {
        return false;
    }
    if (o === true) {
        return o;
    }
    if (Array.isArray(o)) {
        return o.length > 0;
    }
    if (__type(o) === 'Object') {
        return Object.keys(o).length > 0;
    }
    return !!o;
}
"""

CAPITALIZE_FUNCTION = """
function __capitalize(s) {
    return s ? s[0].toUpperCase() + s.substring(1) : s;
}
"""

BATCH_FUNCTION = """
function __batch(arr, size, fillWith) {
    var result = arr.reduce(function (result, value) {

        var curr = result[result.length - 1];
        if (!curr || curr.length === size) {
            result.push([]);
            curr = result[result.length - 1];
        }

        curr.push(value);
        return result;
    }, []);

    var last = result[result.length - 1];
    if (last && last.length < size && fillWith !== undefined) {
        for (var i = 0; i < size - last.length; i++) {
            last.push(fillWith);
        }
    }

    return result;
}
"""

DEFAULT_FUNCTION = """
function __default(obj, defaultValue, boolean) {
    defaultValue = defaultValue === undefined ? '' : defaultValue;
    boolean = boolean === undefined ? false : boolean;

    var test;

    if (boolean === true) {
        if (!obj) {
            test = false;
        }
        else if (Array.isArray(obj)) {
            test = obj.length > 0;
        }
        else {
            try {
                var keys = Object.keys(obj);
                test = keys.length > 0;
            }
            catch (e) {
                test = !!obj;
            }
        }
    }
    else {
        test = obj !== undefined;
    }

    return test ? obj : defaultValue;
}
"""

INT_FUNCTION = """
function __int(value, defaultValue) {
    defaultValue = defaultValue === undefined ? 0 : defaultValue;
    value = parseInt(value, 10);
    return isNaN(value) ? defaultValue : value;
}
"""

SLICE_FUNCTION = """
function __slice(value, slices, fillWith) {
    var hasFillWith = fillWith != null;
    var length = value.length;
    var itemsPerSlice = Math.floor(length / slices);
    var slicesWithExtra = length % slices;
    var offset = 0;
    var result = [];

    for (var i = 0; i < slices; i++) {
        var start = offset + i * itemsPerSlice;

        if (i < slicesWithExtra) {
            offset += 1;
        }

        var end = offset + (i + 1) * itemsPerSlice;
        var tmp = value.slice(start, end);

        if (hasFillWith && i >= slicesWithExtra) {
            tmp.push(fillWith);
        }

        result.push(tmp);
    }

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
    length = length === undefined ? 255 : length;
    killwords = killwords === undefined ? false : killwords;
    end = end === undefined ? '...' : end;

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

EACH_FUNCTION = """
function __each(obj, fn) {
    if (Array.isArray(obj)) {
        return obj.forEach(fn);
    }
    try {
        var keys = Object.keys(obj);
    } catch (e) {
        return;
    }
    keys.forEach(function (k) {
        fn(obj[k], k);
    });
}
"""

FIRST_FUNCTION = """
function __first(obj) {
    return Array.isArray(obj) ? obj[0] : null;
}
"""

LAST_FUNCTION = """
function __last(obj) {
    return Array.isArray(obj) ? obj[obj.length - 1] : null;
}
"""

SIZE_FUNCTION = """
function __size(obj) {
    if (Array.isArray(obj)) {
        return obj.length;
    }
    try {
        var keys = Object.keys(obj);
    }
    catch (e) { return 0; }
    return keys.length;
}
"""

IS_EQUAL_FUNCTION = """
function __isEqual(objA, objB) {
    var typeA;
    var keysA;
    var i;

    if (objA === objB) {
        return true;
    }

    typeA = __type(objA);

    if (typeA !== __type(objB)) {
        return false;
    }

    if (typeA === 'Array') {

        if (objA.length !== objB.length) {
            return false;
        }

        for (i = 0; i < objA.length; i++) {
            if (!__isEqual(objA[i], objB[i])) {
                return false;
            }
        }

        return true;
    }

    if (__type(objA) === 'Object') {
        keysA = Object.keys(objA);

        if (keysA.length !== Object.keys(objB).length) {
            return false;
        }

        for (i = 0; i < keysA.length; i++) {
            if (!__isEqual(objA[keysA[i]], objB[keysA[i]])) {
                return false;
            }
        }

        return true;
    }

    return false;
}
"""

ESCAPE_FUNCTION = """
function __escaper(match) {
    return {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&#34;',
        "'": '&#x27;',
        '`': '&#x60;'
    }[match];
}
var __escapeTestRegex = /(?:&|<|>|"|'|`)/;
var __escapeReplaceRegex = new RegExp(__escapeTestRegex.source, 'g');
function __escape(str) {
    str = str == null ? '' : '' + str;
    return __escapeTestRegex.test(str) ? str.replace(__escapeReplaceRegex, __escaper) : str;
}
"""

# This string has to double all the '{' and '}' due to Python's string formatting.
# See - https://docs.python.org/2/library/string.html#formatstrings
TEMPLATE_WRAPPER = """
function template(context) {{
    var __result = "";
    var __tmp;
    var __toString = Object.prototype.toString;
    function __type(o) {{
        return __toString.call(o).match(/\[object (.*?)\]/)[1];
    }}
    {template_code}
    return __result;
}}
"""
