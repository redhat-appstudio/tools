from subprocess import run, CompletedProcess, CalledProcessError
from verify_rpms.exceptions import CmdError


class CmdRunner:

    @staticmethod
    def run_cmd(args: list[str]) -> CompletedProcess:
        """
        Run a cmd command using subprocess run method.
        Checked flags: check, text, capture_output
        :param args: arguments to pass to the command line
        :return: results of the subprocess
        :throws: CmdError
        """
        try:
            result: CompletedProcess = run(args=args, check=True, text=True, capture_output=True)
        except CalledProcessError as error:
            raise CmdError(f"Running {args} failed\n{error.stderr}")
        except FileNotFoundError as error:
            raise CmdError(f"Running {args} failed\n{error}")
        return result
