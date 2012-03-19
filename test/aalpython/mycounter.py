def log(msg):
    file("/tmp/fmbt.test.aal-python.mycounter.log", "w").write(msg + '\n')

def foo():
    pass

def direction_changed(i):
    log('change %s' % (i,))
    log('    dec called: %s' % (dec_called,))

