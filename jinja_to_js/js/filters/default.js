// for jinja implementation see:
// https://github.com/mitsuhiko/jinja2/blob/master/jinja2/filters.py#L267-L286
function __default(obj, defaultValue, boolean) {
    defaultValue = _.isUndefined(defaultValue) ? '' : defaultValue;
    boolean = _.isUndefined(boolean) ? false : boolean;

    var toString = Object.prototype.toString;
    var test;

    if (boolean === true) {
        test = !o ? false : toString.call(o).match(/\[object (Array|Object)\]/) ? !_.isEmpty(o) : !!o;
    }
    else {
        test = !_.isUndefined(obj);
    }

    return test ? obj : defaultValue;
}
