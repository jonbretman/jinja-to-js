(function (global, factory) {

    if (typeof define === 'function' && define.amd) {
        define(['exports'], factory);
    } else if (typeof exports === 'object' && typeof exports.nodeName !== 'string') {
        factory(exports);
    } else {
        global.jinjaToJS = {};
        factory(global.jinjaToJS);
    }

}(this, function (exports) {

    function escaper(match) {
        return {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&#34;',
            "'": '&#x27;',
            '`': '&#x60;'
        }[match];
    }

    var ESCAPE_TEST_REGEX = /(?:&|<|>|"|'|`)/;
    var ESCAPE_REPLACE_REGEX = new RegExp(ESCAPE_TEST_REGEX.source, 'g');
    var OBJECT_TYPE_REGEX = /\[object (.*?)]/;

    exports.filters = {

        capitalize: function (s) {
            return s ? s[0].toUpperCase() + s.substring(1) : s;
        },

        batch: function (arr, size, fillWith) {
            var batched = arr.reduce(function (result, value) {

                var curr = result[result.length - 1];
                if (!curr || curr.length === size) {
                    result.push([]);
                    curr = result[result.length - 1];
                }

                curr.push(value);
                return result;
            }, []);

            var last = batched[batched.length - 1];
            if (last && last.length < size && fillWith !== undefined) {
                for (var i = 0; i < size - last.length; i++) {
                    last.push(fillWith);
                }
            }

            return batched;
        },

        'default': function (obj, defaultValue, boolean) {
            defaultValue = defaultValue === undefined ? '' : defaultValue;
            boolean = boolean === undefined ? false : boolean;

            var test;

            if (boolean === true) {
                if (!obj) {
                    test = false;
                } else if (Array.isArray(obj)) {
                    test = obj.length > 0;
                } else {
                    try {
                        var keys = Object.keys(obj);
                        test = keys.length > 0;
                    } catch (e) {
                        test = !!obj;
                    }
                }
            } else {
                test = obj !== undefined;
            }

            return test ? obj : defaultValue;
        },

        int: function (value, defaultValue) {
            defaultValue = defaultValue === undefined ? 0 : defaultValue;
            value = parseInt(value, 10);
            return isNaN(value) ? defaultValue : value;
        },

        slice: function (value, slices, fillWith) {
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
        },

        title: function (s) {
            s = s + '';
            return s.split(' ').map(function (word) {
                return word[0].toUpperCase() + word.substring(1).toLowerCase();
            }).join(' ');
        },

        truncate: function (s, length, killwords, end) {
            s = s + '';
            length = length === undefined ? 255 : length;
            killwords = killwords === undefined ? false : killwords;
            end = end === undefined ? '...' : end;

            var endLength = end.length;

            if (s.length <= length) {
                return s;
            } else if (killwords) {
                return s.substring(0, length - endLength) + end;
            }

            s = s.substring(0, length - endLength).split(' ');
            s.pop();
            s = s.join(' ');
            if (s.length < length) {
                s += ' ';
            }
            return s + end;
        },

        first: function (obj) {
            return Array.isArray(obj) ? obj[0] : null;
        },

        last: function (obj) {
            return Array.isArray(obj) ? obj[obj.length - 1] : null;
        },

        size: function (obj) {
            if (Array.isArray(obj)) {
                return obj.length;
            }
            try {
                var keys = Object.keys(obj);
            } catch (e) {
                return 0;
            }
            return keys.length;
        }

    };

    var runtime = exports.runtime = {

        type: function (o) {
            return Object.prototype.toString.call(o).match(OBJECT_TYPE_REGEX)[1];
        },

        boolean: function (o) {
            if (!o) {
                return false;
            }
            if (o === true) {
                return o;
            }
            if (Array.isArray(o)) {
                return o.length > 0;
            }
            if (runtime.type(o) === 'Object') {
                return Object.keys(o).length > 0;
            }
            return !!o;
        },

        each: function (obj, fn) {
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
        },

        isEqual: function (objA, objB) {
            var typeA;
            var keysA;
            var i;

            if (objA === objB) {
                return true;
            }

            typeA = runtime.type(objA);

            if (typeA !== runtime.type(objB)) {
                return false;
            }

            if (typeA === 'Array') {

                if (objA.length !== objB.length) {
                    return false;
                }

                for (i = 0; i < objA.length; i++) {
                    if (!runtime.isEqual(objA[i], objB[i])) {
                        return false;
                    }
                }

                return true;
            }

            if (runtime.type(objA) === 'Object') {
                keysA = Object.keys(objA);

                if (keysA.length !== Object.keys(objB).length) {
                    return false;
                }

                for (i = 0; i < keysA.length; i++) {
                    if (!runtime.isEqual(objA[keysA[i]], objB[keysA[i]])) {
                        return false;
                    }
                }

                return true;
            }

            return false;
        },

        escape: function (str) {
            str = str == null ? '' : '' + str;
            return ESCAPE_TEST_REGEX.test(str) ? str.replace(ESCAPE_REPLACE_REGEX, escaper) : str;
        }

    };

}));
