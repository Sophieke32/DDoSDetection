#!/usr/bin/env python3
"""
    Replacement for the removed `osken-manager`
    This file needs to be run for the controller to work (I suggest making it a service
    in your IDE). Ideally you run it before you run Mininet, though if you do it the other
    way around, Mininet should still update according to this controller.
"""

import logging, sys, signal, os

from os_ken import cfg
from os_ken import log
from os_ken.base.app_manager import AppManager
from os_ken.lib import hub

CONF = cfg.CONF
CONF.register_cli_opts([
    cfg.MultiStrOpt('app', positional=True, default=[],
                    help='application module name or file to run'),
])


def main(args=None):
    CONF(args=args, project='os_ken')
    log.init_log()
    logger = logging.getLogger('run_osken')

    # Always load the OpenFlow handler so switches can connect.
    app_list = ['os_ken.controller.ofp_handler'] + list(CONF.app)

    app_mgr = AppManager.get_instance()
    app_mgr.load_apps(app_list)
    contexts = app_mgr.create_contexts()
    services = app_mgr.instantiate_apps(**contexts)

    # Treat SIGTERM like Ctrl+C so the IDE's stop button also shuts down cleanly.
    signal.signal(signal.SIGTERM, signal.default_int_handler)
    try:
        hub.joinall(services)
    except KeyboardInterrupt:
        logger.debug('Keyboard interrupt, shutting down')
    finally:
        app_mgr.close()
        logging.shutdown()
        sys.stdout.flush()
        sys.stderr.flush()

        # The OpenFlow listener threads are non-daemon and blocked in accept(),
        # so a normal interpreter exit would hang forever. Exit explicitly.
        os._exit(0)


if __name__ == '__main__':
    main(sys.argv[1:])
