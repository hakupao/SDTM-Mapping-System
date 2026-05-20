"""
Textual TUI for SDTM ENSEMBLE pipeline execution.
"""

import os
import subprocess
import threading
from datetime import datetime

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Button,
    Checkbox,
    DataTable,
    Footer,
    Header,
    Label,
    ProgressBar,
    RichLog,
    Static,
)

from sdtm_core import STEPS, get_status, iter_pipeline_events, load_config


class SdtmTui(App):
    """Interactive terminal UI for SDTM pipeline runs."""

    TITLE = 'SDTM ENSEMBLE'
    SUB_TITLE = 'Pipeline TUI'
    BINDINGS = [
        ('a', 'run_all', 'Run all'),
        ('r', 'run_selected', 'Run selected'),
        ('f', 'run_from_selected', 'Run from selected'),
        ('s', 'stop_pipeline', 'Stop'),
        ('u', 'refresh_status', 'Refresh'),
        ('y', 'copy_log', 'Copy log'),
        ('l', 'clear_log', 'Clear log'),
        ('c', 'toggle_continue', 'Continue'),
        ('q', 'quit', 'Quit'),
    ]

    CSS = """
    Screen {
        background: #101418;
        color: #e5e7eb;
    }

    #root {
        height: 1fr;
    }

    #top {
        height: 14;
        min-height: 10;
    }

    #steps-panel {
        width: 3fr;
        border: solid #334155;
    }

    #status-panel {
        width: 2fr;
        border: solid #334155;
    }

    #controls {
        height: 3;
        padding: 0 1;
        background: #151b23;
        content-align: left middle;
    }

    #progress-panel {
        height: 8;
        padding: 1 2;
        border: solid #334155;
    }

    #log-panel {
        height: 1fr;
        border: solid #334155;
    }

    .panel-title {
        height: 1;
        padding: 0 1;
        background: #1f2937;
        color: #f8fafc;
        text-style: bold;
    }

    Button {
        margin-right: 1;
        min-width: 7;
        width: auto;
        content-align: center middle;
    }

    #run-all {
        width: 8;
    }

    #run-selected {
        width: 11;
    }

    #run-from-selected {
        width: 15;
    }

    #stop {
        width: 8;
    }

    #refresh {
        width: 10;
    }

    #copy-log {
        width: 10;
    }

    #clear-log {
        width: 11;
    }

    Checkbox {
        margin-left: 1;
        width: 28;
    }

    DataTable {
        height: 1fr;
    }

    RichLog {
        height: 1fr;
        background: #0b0f14;
    }

    ProgressBar {
        width: 50;
    }
    """

    def __init__(self):
        super().__init__()
        self.cwd = os.getcwd()
        self.config = load_config(self.cwd)
        self.study_id = self.config.get('STUDY_ID', 'UNKNOWN')
        self.continue_on_error = False
        self.pipeline_running = False
        self.stop_event = threading.Event()
        self.worker_thread = None
        self.current_process = None
        self.process_lock = threading.Lock()
        self.log_lines = []
        self.log_path = self._make_log_path()
        self.pipeline_total_steps = 0
        self.pipeline_done_steps = 0

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id='root'):
            yield Label(f'Study: {self.study_id}    Root: {self.cwd}', id='study-line')
            with Horizontal(id='top'):
                with Vertical(id='steps-panel'):
                    yield Static('Pipeline Steps', classes='panel-title')
                    yield DataTable(id='steps-table')
                with Vertical(id='status-panel'):
                    yield Static('Stage Outputs', classes='panel-title')
                    yield DataTable(id='status-table')
            with Horizontal(id='controls'):
                yield Button('All', id='run-all', variant='primary')
                yield Button('Selected', id='run-selected')
                yield Button('From Selected', id='run-from-selected')
                yield Button('Stop', id='stop', variant='error', disabled=True)
                yield Button('Refresh', id='refresh')
                yield Button('Copy Log', id='copy-log')
                yield Button('Clear Log', id='clear-log')
                yield Checkbox('Continue on error', id='continue-check')
            with Vertical(id='progress-panel'):
                yield Label('Pipeline: idle', id='pipeline-label')
                yield ProgressBar(
                    total=100,
                    show_percentage=False,
                    show_eta=False,
                    id='pipeline-progress',
                )
                yield Label('Step: idle', id='step-label')
                yield ProgressBar(
                    total=100,
                    show_percentage=False,
                    show_eta=False,
                    id='step-progress',
                )
            with Vertical(id='log-panel'):
                yield Static('Log', classes='panel-title')
                yield RichLog(id='log', highlight=False, markup=False, wrap=True)
        yield Footer()

    def on_mount(self):
        self.title = f'SDTM ENSEMBLE - {self.study_id}'
        self._populate_steps()
        self._refresh_status_table()
        self.query_one('#steps-table', DataTable).focus()
        self._write_log(
            'Ready. Use buttons or shortcuts: '
            'a=all, r=selected, f=from selected, s=stop, y=copy log.'
        )
        self._write_log(f'Log file: {self.log_path}')

    def on_button_pressed(self, event: Button.Pressed):
        button_id = event.button.id
        if button_id == 'run-all':
            self.action_run_all()
        elif button_id == 'run-selected':
            self.action_run_selected()
        elif button_id == 'run-from-selected':
            self.action_run_from_selected()
        elif button_id == 'stop':
            self.action_stop_pipeline()
        elif button_id == 'refresh':
            self.action_refresh_status()
        elif button_id == 'copy-log':
            self.action_copy_log()
        elif button_id == 'clear-log':
            self.action_clear_log()

    def on_checkbox_changed(self, event: Checkbox.Changed):
        if event.checkbox.id == 'continue-check':
            self.continue_on_error = bool(event.value)

    def action_toggle_continue(self):
        checkbox = self.query_one('#continue-check', Checkbox)
        checkbox.value = not checkbox.value

    def action_copy_log(self):
        text = '\n'.join(self.log_lines)
        if not text:
            self._write_log('No log content to copy.')
            return

        try:
            if os.name == 'nt':
                subprocess.run(
                    [
                        'powershell',
                        '-NoProfile',
                        '-Command',
                        'Set-Clipboard -Value ([Console]::In.ReadToEnd())',
                    ],
                    input=text,
                    text=True,
                    encoding='utf-8',
                    check=True,
                    capture_output=True,
                )
            else:
                subprocess.run(
                    ['pbcopy'],
                    input=text,
                    text=True,
                    encoding='utf-8',
                    check=True,
                    capture_output=True,
                )
        except (OSError, subprocess.CalledProcessError) as exc:
            self._write_log(f'Copy failed. Use log file instead: {self.log_path}')
            self._write_log(f'Copy error: {exc}')
            return

        self._write_log('Copied current log to clipboard.')

    def action_clear_log(self):
        self.log_lines.clear()
        self.query_one('#log', RichLog).clear()

    def action_refresh_status(self):
        self._refresh_status_table()
        self._write_log('Status refreshed.')

    def action_run_all(self):
        self._start_run(1, len(STEPS), 'Run all')

    def action_run_selected(self):
        seq = self._selected_seq()
        self._start_run(seq, seq, f'Run {self._step_id(seq)}')

    def action_run_from_selected(self):
        seq = self._selected_seq()
        self._start_run(seq, len(STEPS), f'Run from {self._step_id(seq)}')

    def action_stop_pipeline(self):
        if not self.pipeline_running:
            return
        self.stop_event.set()
        with self.process_lock:
            proc = self.current_process
        if proc and proc.poll() is None:
            try:
                proc.terminate()
            except OSError:
                pass
        self._write_log('Stop requested. Waiting for current process to exit...')

    def _populate_steps(self):
        table = self.query_one('#steps-table', DataTable)
        table.clear(columns=True)
        table.cursor_type = 'row'
        table.add_column('#', key='seq', width=4)
        table.add_column('ID', key='step_id', width=8)
        table.add_column('Name', key='name', width=16)
        table.add_column('Description', key='desc', width=18)
        table.add_column('Status', key='status', width=12)
        table.add_column('Time', key='time', width=8)
        for seq, module, step_id, name, desc in STEPS:
            table.add_row(str(seq), step_id, name, desc, 'Idle', '-', key=step_id)

    def _refresh_status_table(self):
        table = self.query_one('#status-table', DataTable)
        table.clear(columns=True)
        table.cursor_type = 'none'
        table.add_column('Stage', key='stage', width=18)
        table.add_column('Latest', key='latest', width=20)
        table.add_column('Versions', key='versions', width=12)
        for folder, latest, count in get_status(self.study_id, self.cwd):
            table.add_row(folder, latest, count)

    def _start_run(self, start, end, label):
        if self.pipeline_running:
            self._write_log('A pipeline run is already active.')
            return

        self.pipeline_running = True
        self.stop_event.clear()
        self.pipeline_total_steps = 0
        self.pipeline_done_steps = 0
        self._set_buttons_running(True)
        self._reset_step_status()
        self._reset_progress()
        self._write_log(f'{label}; continue_on_error={self.continue_on_error}')

        self.worker_thread = threading.Thread(
            target=self._run_worker,
            args=(start, end, self.continue_on_error),
            daemon=True,
        )
        self.worker_thread.start()

    def _run_worker(self, start, end, continue_on_error):
        def on_process_start(proc):
            with self.process_lock:
                self.current_process = proc

        def on_process_end(proc):
            with self.process_lock:
                if self.current_process is proc:
                    self.current_process = None

        try:
            for event in iter_pipeline_events(
                start,
                end,
                continue_on_error=continue_on_error,
                cwd=self.cwd,
                stop_requested=self.stop_event.is_set,
                on_process_start=on_process_start,
                on_process_end=on_process_end,
            ):
                self.call_from_thread(self._handle_runner_event, event)
        except Exception as exc:
            self.call_from_thread(self._handle_runner_event, {
                'kind': 'fatal',
                'message': f'{type(exc).__name__}: {exc}',
            })

    def _handle_runner_event(self, event):
        kind = event['kind']
        if kind == 'pipeline_start':
            selected = event['selected']
            self.pipeline_total_steps = len(selected)
            self.pipeline_done_steps = 0
            first_step = selected[0][2] if selected else 'pipeline'
            self._set_pipeline_progress(0, self.pipeline_total_steps, first_step)
        elif kind == 'step_start':
            self._mark_step(event['step_id'], 'Running', '-')
            self._set_pipeline_progress(
                self.pipeline_done_steps,
                self.pipeline_total_steps,
                f"{event['step_id']} running",
            )
            self._set_step_progress(0, 100, f"{event['step_id']} running")
            self._write_log(
                f"[{event['step_id']}] start {event['name']} - {event['desc']}"
            )
        elif kind == 'progress':
            total = max(event['total'], 1)
            desc = event['desc'] or event['step_id']
            self._set_step_progress(
                event['current'],
                total,
                f"{event['step_id']} {desc}",
            )
        elif kind == 'log':
            self._write_log(event['line'])
        elif kind == 'step_end':
            status = event['status']
            elapsed = f"{event['elapsed']:.1f}s"
            self._mark_step(event['step_id'], status, elapsed)
            self.pipeline_done_steps += 1
            self._set_pipeline_progress(
                self.pipeline_done_steps,
                self.pipeline_total_steps,
                f"{event['step_id']} {status}",
            )
            self._set_step_progress(100, 100, f"{event['step_id']} {status}")
            self._write_log(f"[{event['step_id']}] {status} ({elapsed})")
        elif kind == 'pipeline_end':
            self._finish_run(event)
        elif kind == 'error':
            self._write_log(f"[ERROR] {event['message']}")
            self._finish_run({'results': [], 'failed': [], 'elapsed': 0})
        elif kind == 'fatal':
            self._write_log(f"[FATAL] {event['message']}")
            self._finish_run({'results': [], 'failed': [event], 'elapsed': 0})

    def _finish_run(self, event):
        results = event.get('results', [])
        failed = event.get('failed', [])
        elapsed = event.get('elapsed', 0)
        attempted = len(results)
        total = self.pipeline_total_steps or max(attempted, 1)
        self.pipeline_done_steps = attempted
        self._set_pipeline_progress(attempted, total, 'finished')
        if failed:
            failed_ids = ', '.join(item.get('step_id', 'pipeline') for item in failed)
            self._write_log(
                f'Pipeline finished with failures: {failed_ids}; '
                f'elapsed={elapsed:.1f}s'
            )
        else:
            self._write_log(
                f'Pipeline finished successfully: {attempted} step(s); '
                f'elapsed={elapsed:.1f}s'
            )
        self._refresh_status_table()
        self.pipeline_running = False
        self._set_buttons_running(False)

    def _reset_step_status(self):
        for seq, module, step_id, name, desc in STEPS:
            self._mark_step(step_id, 'Idle', '-')

    def _mark_step(self, step_id, status, elapsed):
        table = self.query_one('#steps-table', DataTable)
        try:
            table.update_cell(step_id, 'status', status)
            table.update_cell(step_id, 'time', elapsed)
        except KeyError:
            pass

    def _reset_progress(self):
        self._set_pipeline_progress(0, 100, 'idle')
        self._set_step_progress(0, 100, 'idle')

    def _set_pipeline_progress(self, current, total, label):
        progress = self.query_one('#pipeline-progress', ProgressBar)
        pct = int(current / max(total, 1) * 100)
        progress.update(total=100, progress=pct)
        self.query_one('#pipeline-label', Label).update(
            f'Pipeline: {current}/{total}  {pct}%  {label}'
        )

    def _set_step_progress(self, current, total, label):
        progress = self.query_one('#step-progress', ProgressBar)
        pct = int(current / max(total, 1) * 100)
        progress.update(total=100, progress=pct)
        self.query_one('#step-label', Label).update(
            f'Step: {current}/{total}  {pct}%  {label}'
        )

    def _set_buttons_running(self, running):
        for button_id in ('#run-all', '#run-selected', '#run-from-selected', '#refresh'):
            self.query_one(button_id, Button).disabled = running
        self.query_one('#stop', Button).disabled = not running

    def _write_log(self, line):
        line = str(line)
        self.log_lines.append(line)
        with open(self.log_path, 'a', encoding='utf-8') as log_file:
            log_file.write(line + '\n')
        log = self.query_one('#log', RichLog)
        log.write(line)

    def _make_log_path(self):
        logs_dir = os.path.join(self.cwd, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        stamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return os.path.join(logs_dir, f'sdtm_tui_{stamp}.log')

    def _selected_seq(self):
        table = self.query_one('#steps-table', DataTable)
        row = table.cursor_coordinate.row
        if row is None or row < 0 or row >= len(STEPS):
            return 1
        return STEPS[row][0]

    def _step_id(self, seq):
        for step in STEPS:
            if step[0] == seq:
                return step[2]
        return str(seq)


def main():
    SdtmTui().run()


if __name__ == '__main__':
    main()
