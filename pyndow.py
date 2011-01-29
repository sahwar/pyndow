from functools import partial
import sys
import time
import traceback

import xcb, xcb.xproto

import util
import icccm
import ewmh
import event

import state
import root
import config
import window
import events
import grab
import command
import client
import misc
import popup.cycle

aid = partial(util.get_atom, state.conn)

util.build_atom_cache(state.conn, icccm)
util.build_atom_cache(state.conn, ewmh)

command.init()

state.conn.core.ChangeWindowAttributesChecked(
    state.root,
    xcb.xproto.CW.EventMask | xcb.xproto.CW.Cursor,
    [xcb.xproto.EventMask.SubstructureNotify |
     xcb.xproto.EventMask.SubstructureRedirect |
     xcb.xproto.EventMask.PropertyChange |
     xcb.xproto.EventMask.FocusChange, state.cursors['LeftPtr']]
).check()

events.register_callback(xcb.xproto.ClientMessageEvent,
                         root.cb_ClientMessage, state.root)
events.register_callback(xcb.xproto.MappingNotifyEvent,
                         root.cb_MappingNotifyEvent, state.root)
events.register_callback(xcb.xproto.MapRequestEvent,
                         client.cb_MapRequestEvent, state.root)
events.register_callback(xcb.xproto.FocusInEvent,
                         client.cb_FocusInEvent, state.root)
events.register_callback(xcb.xproto.FocusOutEvent,
                         client.cb_FocusOutEvent, state.root)
events.register_callback(xcb.xproto.ConfigureRequestEvent,
                         window.cb_ConfigureRequestEvent, state.root)
events.register_callback(xcb.xproto.MotionNotifyEvent, grab.drag_do,
                         state.pyndow, None, None, None)
events.register_callback(xcb.xproto.ButtonReleaseEvent, grab.drag_end,
                         state.pyndow, None, None, None)

#events.register_keygrab(popup.cycle.start, popup.cycle.do_next,
                        #popup.cycle.end, state.root,
                        #config.get_option('cycle_next'), 'Alt_L')

#events.register_keygrab(popup.cycle.start, popup.cycle.do_prev,
                        #popup.cycle.end, state.root,
                        #config.get_option('cycle_prev'), 'Alt_L')

k_cyc_n = config.get_option('cycle_next')
k_cyc_p = config.get_option('cycle_prev')

events.register_keypress(popup.cycle.start_next, state.root, k_cyc_n)
events.register_keypress(popup.cycle.do_next, state.pyndow, k_cyc_n)

events.register_keypress(popup.cycle.start_prev, state.root, k_cyc_p)
events.register_keypress(popup.cycle.do_prev, state.pyndow, k_cyc_p)

events.register_keyrelease(popup.cycle.end, state.pyndow, 'Alt_L')
events.register_keyrelease(popup.cycle.end, state.pyndow, 'Alt_R')

state.root_focus()

while True:
    event.read(state.conn, block=True)
    for e in event.queue():
        events.dispatch(e)

    events.run_latent()

    state.conn.flush()

    if state.die:
        break

misc.spawn('killall Xephyr')