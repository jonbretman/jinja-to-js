// for jinja implementation see:
// https://github.com/mitsuhiko/jinja2/blob/master/jinja2/filters.py#L458-L483
function __truncate(s, length, killWords, end) {
    s = s + '';
    killWords = _.isUndefined(killWords) ? false : killWords;
    end = _.isUndefined(end) ? '...' : end;

    var endLength = end.length;

    if (s.length < length) {
        return s;
    }

    if (killWords) {
        return s.substring(0, length - endLength) + end;
    }

    s = s.split(' ');
    s.pop();
    s = s.join(' ');

    if (s.length < length) {
        s += ' ';
    }

    return s + end;
}
