import json
import deoplete.util
import os

from deoplete.logger import getLogger
from subprocess import Popen, PIPE
from .base import Base

log = getLogger('logging')

CONFIG_FILE = '.flowconfig'

def find_config_directory(root):
    for files in os.listdir(root):
        if CONFIG_FILE in files:
            return root
        elif root == '/':
            return None
        else:
            return find_config_directory(os.path.dirname(root))

class Source(Base):
    def __init__(self, vim):
        Base.__init__(self, vim);

        self.flow_bin = self.vim.vars['deoplete#sources#flow#flow_bin'] or 'flow'
        self.rank = 600
        self.name = 'flow'
        self.mark = '[FL]'
        self.min_pattern_length = 0
        self.filetypes = ['javascript']
        self._project_directory = None

    def get_complete_position(self, context):
        pos = context['input'].rfind('.')
        return pos if pos < 0 else pos + 1

    def relative_file(self):
        if not self._project_directory:
            current_directory = self.vim.eval("expand('%:p:h')")
            self._project_directory = find_config_directory(current_directory)

        filename = self.vim.eval("expand('%:p')")

        return filename[len(self._project_directory) + 1:]

    def gather_candidates(self, context):
        file_name = self.relative_file()
        line = str(self.vim.current.window.cursor[0])
        column = str(self.vim.current.window.cursor[1] + 1)
        command = [self.flow_bin, 'autocomplete', '--json', '--no-auto-start', file_name, line, column]

        log.debug(command)
        buf = '\n'.join(self.vim.current.buffer[:])

        try:
            process = Popen(command, stdout=PIPE, stdin=PIPE)
            command_results = process.communicate(input=str.encode(buf))[0]

            if process.returncode != 0:
                return []

            results = json.loads(command_results.decode('utf-8'))

            return [{'word': x['name'], 'kind': x['type']} for x in results['result']]
        except FileNotFoundError:
            pass # ignore file not found error
