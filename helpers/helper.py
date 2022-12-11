import psutil

class Helper:

    def __init__(self) -> None:
        pass

    def pid_exists(self, pid: int) -> bool:
        ''' Check whether pid exists in the current process table. '''
        for p in psutil.process_iter():
            if p.pid == pid:
                print(f'Process {pid} exists')
        return psutil.pid_exists(pid)