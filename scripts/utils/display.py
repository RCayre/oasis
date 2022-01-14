import sys

def progress(count, total, suffix=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '#' * filled_len + ' ' * (bar_len - filled_len)
    sys.stdout.write("\r"+"  "*100)
    sys.stdout.flush()

    message = "\r"+'[%s] %s%s ...%s' % (bar, percents, '%', suffix)
    sys.stdout.write(message)
