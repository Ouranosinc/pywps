##################################################################
# Copyright 2016 OSGeo Foundation,                               #
# represented by PyWPS Project Steering Committee,               #
# licensed under MIT, Please consult LICENSE.txt for details     #
##################################################################

import os
import sys
import tempfile
import pywps.configuration as config
from pywps.processing.basic import Processing

import logging
LOGGER = logging.getLogger("PYWPS")


SLURM_TMPL = """\
#!/bin/bash
#SBATCH -e /tmp/{pid}.err
#SBATCH -o /tmp/{pid}.out
#SBATCH -J {pid}
#SBATCH --time=00:30:00
#set -eo pipefail -o nounset
export PATH="{prefix}/bin:$PATH"
source activate {env};launch "{filename}"
"""


def secure_copy(source, target, host=None):
    """
    Copy source file to remote host.
    """
    from pathos.secure import Copier
    host = host or "localhost"
    copier = Copier(source)
    destination = '{}:{}'.format(host, target)
    copier.config(source=source, destination=destination)
    copier.launch()
    LOGGER.debug("copied source=%s, destination=%s", source, destination)


def sbatch(filename, host=None):
    from pathos import SSH_Launcher
    host = host or "localhost"
    launcher = SSH_Launcher("sbatch")
    launcher.config(command="sbatch {}".format(filename), host=host, background=False)
    launcher.launch()
    LOGGER.info("Starting slurm job: %s", launcher.response())


class Slurm(Processing):

    def _build_submit_file(self, dump_file_name):
        workdir = config.get_config_value('server', 'workdir')
        submit_file_name = tempfile.mkstemp(prefix='slurm_', suffix='.submit', dir=workdir)[1]
        with open(submit_file_name, 'w') as fp:
            fp.write(SLURM_TMPL.format(
                pid=self.job.process.uuid,
                env='emu',
                prefix='/home/pingu/anaconda',
                filename=dump_file_name))

    def start(self):
        host = config.get_config_value('extra', 'host')
        # dump job to file
        dump_file_name = self.job.dump()
        # copy dumped job to remote host
        # secure_copy(source=dump_file_name, target="/tmp/marshalled", host=host)
        # write submit script
        submit_file_name = self._build_submit_file(dump_file_name)
        # copy submit file to remote
        # secure_copy(source=submit_file_name, target="/tmp/emu.submit", host=host)
        # run remote pywps process
        sbatch(filename=submit_file_name, host=host)
