from settings import APP_ROOT

def add_signs(val, k):
    val = str(val)
    if len(val) < k:
        val = ('0' * (k - len(val))) + val
    return val


def form_date(day, month, year):
    return int(add_signs(year, 4) + add_signs(month, 2) + add_signs(day, 2))


def form_string_date(day, month, year):
    return add_signs(day, 2) + '.' + add_signs(month, 2) + '.' + add_signs(year, 4)


def check_name(name):
    return name.find('&') == -1 and name.find('-') == -1


MONTHS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
