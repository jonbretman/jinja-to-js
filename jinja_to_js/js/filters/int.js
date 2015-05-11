function __int(value, defaultValue) {
    defaultValue = _.isUndefined(defaultValue) ? 0 : defaultValue;
    value = parseInt(value, 10);
    return isNaN(value) ? defaultValue : value;
}
