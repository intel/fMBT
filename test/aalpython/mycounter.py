log_filename="/tmp/fmbt.test.aal-python.mycounter.log"
file(log_filename, "w").close()
def log(msg):
    file(log_filename, "a").write(msg + "\n")

def foo():
    pass

def direction_changed(i):
    log('change direction on value %s' % (i,))
    log('    dec called: %s' % (dec_called,))

