# Reloj virtual: el tiempo solo avanza cuando el programa "duerme"
import time as _t
class StopTest(Exception): pass
AHORA = [0]
HOOK_TICK = [None]    # se llama en cada sleep_ms(10) del bucle del gateway
HOOK_SLEEP = [None]   # se llama en cada sleep(s)
def ticks_ms(): return AHORA[0]
def ticks_diff(a, b): return a - b
def sleep_ms(ms):
    AHORA[0] += ms
    if ms == 10 and HOOK_TICK[0]: HOOK_TICK[0]()
def sleep(s):
    AHORA[0] += int(s * 1000)
    if HOOK_SLEEP[0]: HOOK_SLEEP[0](s)
